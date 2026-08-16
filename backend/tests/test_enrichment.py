"""Tests for Phase 2: IOC enrichment."""
import pytest

from app.services import ioc_utils
from app.services.enrichment_service import enrich_indicator
from app.services.mitre_mapping import map_alert_to_techniques


# ---- IOC parsing/classification ----

def test_classify_public_ip():
    result = ioc_utils.classify_ip("8.8.8.8")
    assert result["is_public"] is True
    assert result["is_private"] is False


def test_classify_private_ip():
    result = ioc_utils.classify_ip("10.0.0.5")
    assert result["is_private"] is True
    assert result["is_public"] is False


def test_is_domain_true_for_valid_domain():
    assert ioc_utils.is_domain("evil-domain.example.com") is True


def test_is_domain_false_for_ip():
    assert ioc_utils.is_domain("8.8.8.8") is False


def test_detect_hash_algo_sha256():
    assert ioc_utils.detect_hash_algo("a" * 64) == "sha256"


def test_detect_hash_algo_invalid():
    assert ioc_utils.detect_hash_algo("not-a-hash") is None


def test_normalize_indicator_type_mismatch_raises():
    with pytest.raises(ValueError):
        ioc_utils.normalize_indicator_type("ip", "not-an-ip")


# ---- Enrichment (demo mode - no VT key set in test env) ----

@pytest.mark.asyncio
async def test_enrich_private_ip_never_calls_external_provider():
    result = await enrich_indicator("ip", "192.168.1.5")
    assert result.is_public is False
    assert result.provider == "internal"
    assert result.source == "demo"


@pytest.mark.asyncio
async def test_enrich_public_ip_falls_back_to_demo_without_key():
    result = await enrich_indicator("ip", "1.1.1.1")
    assert result.source == "demo"
    assert result.virustotal is not None
    assert result.geo is not None


@pytest.mark.asyncio
async def test_enrich_is_deterministic_for_same_value():
    r1 = await enrich_indicator("ip", "185.220.101.5")
    r2 = await enrich_indicator("ip", "185.220.101.5")
    # second call should be served from cache
    assert r2.source in ("cached", "demo")
    assert r1.virustotal.malicious == r2.virustotal.malicious


@pytest.mark.asyncio
async def test_enrich_hash_demo_mode():
    result = await enrich_indicator("hash", "a" * 64)
    assert result.indicator_type == "hash"
    assert result.source == "demo"


@pytest.mark.asyncio
async def test_enrich_unsupported_type_raises():
    with pytest.raises(ValueError):
        await enrich_indicator("carrier_pigeon", "x")


# ---- MITRE mapping ----

def test_mitre_mapping_brute_force():
    techniques = map_alert_to_techniques("SSH Brute Force Detected", "")
    assert any(t.technique_id == "T1110" for t in techniques)


def test_mitre_mapping_no_match_returns_empty():
    techniques = map_alert_to_techniques("Benign Admin Activity", "routine maintenance")
    assert techniques == []


def test_mitre_mapping_powershell():
    techniques = map_alert_to_techniques("Suspicious PowerShell Execution", "-enc command")
    assert any(t.technique_id == "T1059.001" for t in techniques)
