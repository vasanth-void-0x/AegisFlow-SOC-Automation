"""Tests for VirusTotal client error handling and the enrichment API,
using monkeypatched provider calls (no real network access)."""
import pytest

from app.integrations import virustotal_client as vt
from app.services import enrichment_service


@pytest.mark.asyncio
async def test_provider_timeout_falls_back_to_demo(monkeypatch):
    async def fake_lookup_ip(ip):
        raise vt.VirusTotalError("VirusTotal request timed out")

    monkeypatch.setattr(enrichment_service, "get_settings", lambda: _fake_settings_with_key())
    monkeypatch.setattr(vt, "lookup_ip", fake_lookup_ip)

    result = await enrichment_service.enrich_ip("8.8.4.4")
    assert result.source == "demo"


@pytest.mark.asyncio
async def test_provider_rate_limit_falls_back_to_demo(monkeypatch):
    async def fake_lookup_ip(ip):
        raise vt.VirusTotalRateLimitError("rate limited", status_code=429)

    monkeypatch.setattr(enrichment_service, "get_settings", lambda: _fake_settings_with_key())
    monkeypatch.setattr(vt, "lookup_ip", fake_lookup_ip)

    result = await enrichment_service.enrich_ip("9.9.9.9")
    assert result.source == "demo"


@pytest.mark.asyncio
async def test_provider_live_success_path(monkeypatch):
    async def fake_lookup_ip(ip):
        return {
            "data": {
                "attributes": {
                    "last_analysis_stats": {"malicious": 3, "suspicious": 1, "harmless": 60, "undetected": 6},
                    "reputation": -5,
                    "country": "US",
                    "asn": 15169,
                    "as_owner": "GOOGLE",
                }
            }
        }

    monkeypatch.setattr(enrichment_service, "get_settings", lambda: _fake_settings_with_key())
    monkeypatch.setattr(vt, "lookup_ip", fake_lookup_ip)

    result = await enrichment_service.enrich_ip("8.8.8.9")
    assert result.source == "live"
    assert result.virustotal.malicious == 3
    assert result.geo.country == "US"


def test_enrich_api_endpoint(client):
    resp = client.get("/api/v1/enrich", params={"indicator_type": "ip", "value": "8.8.8.8"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "demo"


def test_enrich_api_endpoint_invalid_value(client):
    resp = client.get("/api/v1/enrich", params={"indicator_type": "ip", "value": "not-an-ip"})
    assert resp.status_code == 422


def test_incident_enrichment_endpoint(client):
    alert = {
        "source": "wazuh",
        "alert_name": "SSH Brute Force Detected",
        "severity": "high",
        "description": "test",
        "source_ip": "203.0.113.55",
        "event_time": "2026-08-12T06:00:00Z",
        "indicators": [{"type": "ip", "value": "203.0.113.55"}],
    }
    created = client.post("/api/v1/alerts", json=alert).json()
    resp = client.get(f"/api/v1/incidents/{created['id']}/enrichment")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["mitre_techniques"][0]["technique_id"] == "T1110"


def _fake_settings_with_key():
    from app.core.config import Settings

    return Settings(virustotal_api_key="fake-key-for-test")
