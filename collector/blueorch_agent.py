#!/usr/bin/env python3
"""BlueOrch Windows Event Log collector with heartbeat and disk-backed retry."""
import argparse
import json
import socket
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.1.0"


def request(config: dict, path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{config['api_url'].rstrip('/')}{path}", data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-BlueOrch-Agent-Key": config["api_key"]}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.loads(response.read())


def heartbeat(config: dict) -> None:
    request(config, "/api/v1/agents/heartbeat", {"hostname": socket.gethostname(), "agent_version": VERSION})


def channels(profile: str) -> list[str]:
    if profile == "security": return ["Security"]
    if profile == "system": return ["Security", "System"]
    return ["Security", "System", "Application"]


def query_windows(channel: str, after: int, limit: int = 100) -> list[dict]:
    script = (
        "$ErrorActionPreference='Stop';"
        f"Get-WinEvent -FilterHashtable @{{LogName='{channel}';StartTime=(Get-Date).AddMinutes(-10)}} -MaxEvents {limit} -ErrorAction SilentlyContinue | "
        f"Where-Object {{$_.RecordId -gt {after}}} | Sort-Object RecordId | "
        "Select-Object RecordId,Id,LevelDisplayName,ProviderName,TimeCreated,MachineName,Message | ConvertTo-Json -Compress"
    )
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, text=True, timeout=45)
    if result.returncode != 0: raise RuntimeError(result.stderr.strip() or f"Unable to read {channel}")
    if not result.stdout.strip(): return []
    value = json.loads(result.stdout)
    return value if isinstance(value, list) else [value]


def normalize(item: dict, channel: str, source_name: str) -> dict:
    level = str(item.get("LevelDisplayName") or "Information").lower()
    severity = "high" if level in {"critical", "error"} else "medium" if level == "warning" else "low"
    windows_event_id = int(item.get("Id") or 0)
    if windows_event_id in {1102, 4698, 4720, 4728, 4732}:
        severity = "high"
    elif windows_event_id in {4625, 4740, 4771}:
        severity = "medium"
    return {
        "message": str(item.get("Message") or f"Windows event {item.get('Id')}")[:20000],
        "source_type": "agent", "source_name": source_name, "hostname": socket.gethostname(),
        "timestamp": item.get("TimeCreated") or datetime.now(timezone.utc).isoformat(), "severity": severity,
        "event_id": f"{socket.gethostname()}:{channel}:{item['RecordId']}",
        "fields": {"event_id": item.get("Id"), "record_id": item.get("RecordId"), "channel": channel,
                   "provider": item.get("ProviderName"), "event_name": f"Windows {channel} Event {item.get('Id')}"},
    }


def load_json(path: Path, default):
    try: return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError): return default


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def run(config: dict, once: bool = False) -> None:
    state_path = Path(config.get("state_file", "blueorch-agent-state.json"))
    spool_path = Path(config.get("spool_file", "blueorch-agent-spool.json"))
    state, spool = load_json(state_path, {}), load_json(spool_path, [])
    interval = max(5, int(config.get("poll_seconds", 15)))
    while True:
        try:
            heartbeat(config)
            for channel in channels(config.get("profile", "security")):
                for item in query_windows(channel, int(state.get(channel, 0))):
                    spool.append(normalize(item, channel, config["source_name"]))
                    state[channel] = max(int(state.get(channel, 0)), int(item["RecordId"]))
            save_json(state_path, state)
            while spool:
                batch = spool[:100]
                # BlueOrch owns ingestion and persistence. n8n V2 polls durable
                # incidents from the backend instead of receiving raw endpoint logs.
                result = request(config, "/api/v1/agents/logs/bulk", {"logs": batch})
                spool = spool[len(batch):]
                save_json(spool_path, spool)
                print(f"sent={result['accepted']} duplicates={result['duplicates']} queued={len(spool)}", flush=True)
        except Exception as exc:
            save_json(spool_path, spool)
            print(f"collector retry: {exc}", flush=True)
        if once: break
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="BlueOrch Windows Event Log collector")
    parser.add_argument("--config", type=Path, default=Path("blueorch-agent.json"))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    config = load_json(args.config, None)
    if not config: raise SystemExit(f"Missing or invalid config: {args.config}")
    run(config, args.once)


if __name__ == "__main__": main()
