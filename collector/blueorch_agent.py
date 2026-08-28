#!/usr/bin/env python3
"""Small dependency-free BlueOrch file-tail collector for Windows and Linux."""
import argparse
import json
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path


def send(api_url: str, api_key: str, source_name: str, message: str, event_id: str) -> None:
    payload = json.dumps({
        "message": message,
        "source_type": "agent",
        "source_name": source_name,
        "hostname": socket.gethostname(),
        "event_id": event_id,
    }).encode()
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/api/v1/logs/ingest",
        data=payload,
        headers={"Content-Type": "application/json", "X-BlueOrch-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.loads(response.read())
            print(f"sent {result['id']} severity={result['severity']}")
    except urllib.error.HTTPError as exc:
        if exc.code == 409:
            print("duplicate skipped")
        else:
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuously forward a log file to BlueOrch")
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--source-name", default="endpoint-file")
    parser.add_argument("--from-start", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    with args.file.open("r", encoding="utf-8", errors="replace") as handle:
        if not args.from_start:
            handle.seek(0, 2)
        while True:
            position = handle.tell()
            line = handle.readline()
            if line:
                message = line.strip()
                if message:
                    send(args.api_url, args.api_key, args.source_name, message, f"{args.file}:{position}")
                continue
            if args.once:
                break
            time.sleep(1)


if __name__ == "__main__":
    main()
