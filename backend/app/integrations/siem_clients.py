"""Read-only Splunk and Wazuh clients with a shared normalized alert format."""
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
import httpx
from app.models.incident import Severity
from app.models.siem_connection import SiemProvider
from app.schemas.incident import AlertIngest, Indicator

class SiemError(RuntimeError): pass

def severity(value: Any) -> Severity:
    text = str(value or "").lower()
    try:
        level = int(text)
        return Severity.critical if level >= 12 else Severity.high if level >= 8 else Severity.medium if level >= 4 else Severity.low
    except ValueError:
        return {"critical": Severity.critical, "high": Severity.high, "medium": Severity.medium}.get(text, Severity.low)

def event_time(value: Any) -> datetime:
    try: return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError): return datetime.now(timezone.utc)

def indicators(src, dst): return [Indicator(type="ip", value=str(x)) for x in (src, dst) if x]

class BaseSiemClient(ABC):
    def __init__(self, base_url, verify_ssl, timeout):
        self.base_url, self.verify_ssl, self.timeout = base_url.rstrip("/"), verify_ssl, timeout
    @abstractmethod
    async def test(self): ...
    @abstractmethod
    async def fetch_alerts(self, limit): ...

class SplunkClient(BaseSiemClient):
    def __init__(self, base_url, token, index_name, verify_ssl, timeout):
        super().__init__(base_url, verify_ssl, timeout); self.token, self.index_name = token, index_name or "*"
    async def request(self, method, path, **kwargs):
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
                response = await client.request(method, self.base_url + path, headers={"Authorization": f"Bearer {self.token}"}, **kwargs)
                response.raise_for_status(); return response
        except httpx.HTTPError as exc: raise SiemError(f"Splunk connection failed: {exc}") from exc
    async def test(self): await self.request("GET", "/services/server/info", params={"output_mode": "json"})
    async def fetch_alerts(self, limit):
        response = await self.request("POST", "/services/search/jobs/export", data={"search": f"search index={self.index_name} earliest=-24h | head {limit}", "output_mode": "json"})
        output = []
        for line in response.text.splitlines():
            try: event = json.loads(line).get("result", {})
            except json.JSONDecodeError: continue
            src, dst = event.get("src_ip") or event.get("src"), event.get("dest_ip") or event.get("dest")
            output.append(AlertIngest(source="splunk", alert_name=str(event.get("alert_name") or event.get("rule_name") or event.get("signature") or "Splunk security event"), severity=severity(event.get("severity")), description=str(event.get("description") or event.get("message") or ""), source_ip=src, destination_ip=dst, hostname=event.get("host"), username=event.get("user"), event_time=event_time(event.get("_time")), raw_event=event, indicators=indicators(src, dst), idempotency_key=str(event.get("event_id") or event.get("_cd") or "") or None))
        return output

class WazuhClient(BaseSiemClient):
    """Pulls alerts from the Wazuh Indexer (OpenSearch, normally port 9200)."""
    def __init__(self, base_url, username, password, index_name, verify_ssl, timeout):
        super().__init__(base_url, verify_ssl, timeout)
        self.username, self.password, self.index_name = username, password, index_name or "wazuh-alerts-*"
    async def get(self, path, params=None, json_body=None):
        try:
            async with httpx.AsyncClient(verify=self.verify_ssl, timeout=self.timeout) as client:
                response = await client.request("GET", self.base_url + path, auth=(self.username, self.password), params=params, json=json_body)
                response.raise_for_status(); return response.json()
        except (httpx.HTTPError, ValueError) as exc: raise SiemError(f"Wazuh Indexer request failed: {exc}") from exc
    async def test(self): await self.get("/")
    async def fetch_alerts(self, limit):
        query = {"size": limit, "sort": [{"timestamp": {"order": "desc"}}], "query": {"range": {"timestamp": {"gte": "now-24h"}}}}
        payload = await self.get(f"/{self.index_name}/_search", json_body=query); output = []
        for hit in payload.get("hits", {}).get("hits", []):
            event = hit.get("_source", {})
            rule, agent, data = event.get("rule", {}), event.get("agent", {}), event.get("data", {})
            src, dst = data.get("srcip"), data.get("dstip")
            output.append(AlertIngest(source="wazuh", alert_name=str(rule.get("description") or "Wazuh security event"), severity=severity(rule.get("level")), description=str(event.get("full_log") or ""), source_ip=src, destination_ip=dst, hostname=agent.get("name"), username=data.get("srcuser") or data.get("dstuser"), event_time=event_time(event.get("timestamp")), raw_event=event, indicators=indicators(src, dst), idempotency_key=str(hit.get("_id") or "") or None))
        return output

def build_client(provider: SiemProvider, credentials, base_url, index_name, verify_ssl, timeout):
    if provider == SiemProvider.splunk: return SplunkClient(base_url, credentials["token"], index_name, verify_ssl, timeout)
    return WazuhClient(base_url, credentials["username"], credentials["password"], index_name, verify_ssl, timeout)
