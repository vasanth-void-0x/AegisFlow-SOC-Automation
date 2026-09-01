"""
Phase 2: IOC enrichment orchestration.

Flow per indicator:
  1. Classify type (ip/domain/url/hash) and public/private for IPs.
  2. Private IPs are never sent to external providers.
  3. Check TTL cache -> return cached result if present.
  4. If VirusTotal key configured, attempt a live call.
  5. Provider failures are returned explicitly. Synthetic verdicts are only
     allowed when DEMO_MODE=true and can never be mistaken for live data.
  6. Always attach MITRE technique mapping derived from the parent alert.
"""
import hashlib

from app.core.config import get_settings
from app.core.logging import get_logger
from app.integrations import virustotal_client as vt
from app.schemas.enrichment import (
    EnrichmentResult,
    GeoInfo,
    MitreTechnique,
    ProviderStatus,
    ResultSource,
    VirusTotalSummary,
)
from app.services import ioc_utils
from app.services.cache import get_enrichment_cache

logger = get_logger(__name__)


def _demo_vt_summary(value: str) -> VirusTotalSummary:
    """Deterministic pseudo-random-but-stable demo verdict based on the value's hash."""
    digest = int(hashlib.sha256(value.encode()).hexdigest(), 16)
    malicious = digest % 6  # 0-5 engines flag it, deterministic per value
    total = 70
    return VirusTotalSummary(
        malicious=malicious,
        suspicious=(digest >> 4) % 3,
        harmless=total - malicious,
        undetected=0,
        total_engines=total,
        reputation=-malicious * 10,
    )


def _demo_geo(ip: str) -> GeoInfo:
    digest = int(hashlib.sha256(ip.encode()).hexdigest(), 16)
    countries = ["US", "DE", "SG", "IN", "NL", "RU", "CN", "BR"]
    return GeoInfo(
        country=countries[digest % len(countries)],
        city="Demo-City",
        asn=f"AS{10000 + (digest % 50000)}",
        org="Demo ISP (no live GeoIP provider configured)",
    )


def _provider_failure(
    *, indicator_type: str, value: str, status: ProviderStatus, message: str, is_public: bool | None = None
) -> EnrichmentResult:
    return EnrichmentResult(
        indicator_type=indicator_type,
        value=value,
        is_public=is_public,
        source=ResultSource.unavailable,
        provider="virustotal",
        provider_status=status,
        error=message,
        raw={"verdict_available": False},
    )


def _demo_result(indicator_type: str, value: str, is_public: bool | None = None) -> EnrichmentResult:
    return EnrichmentResult(
        indicator_type=indicator_type,
        value=value,
        is_public=is_public,
        source=ResultSource.demo,
        provider="demo",
        provider_status=ProviderStatus.demo,
        virustotal=_demo_vt_summary(value),
        geo=_demo_geo(value) if indicator_type == "ip" else None,
        raw={"note": "synthetic demo verdict; not VirusTotal data", "verdict_available": False},
    )


def _classify_provider_error(exc: vt.VirusTotalError) -> ProviderStatus:
    if isinstance(exc, vt.VirusTotalAuthError):
        return ProviderStatus.authentication_failed
    if isinstance(exc, vt.VirusTotalRateLimitError):
        return ProviderStatus.rate_limited
    if isinstance(exc, vt.VirusTotalNotFoundError):
        return ProviderStatus.not_found
    if isinstance(exc, vt.VirusTotalTimeoutError):
        return ProviderStatus.timeout
    return ProviderStatus.unavailable


async def enrich_ip(ip: str) -> EnrichmentResult:
    settings = get_settings()
    cache = get_enrichment_cache()
    classification = ioc_utils.classify_ip(ip)

    if classification["is_private"]:
        return EnrichmentResult(
            indicator_type="ip",
            value=ip,
            is_public=False,
            source=ResultSource.unavailable,
            provider="internal",
            provider_status=ProviderStatus.not_applicable,
            raw={"note": "private/internal IP - not sent to external providers"},
        )

    cache_key = f"ip:{ip}"
    cached = cache.get(cache_key)
    if cached is not None:
        cached.source = ResultSource.cached
        cached.provider_status = ProviderStatus.cached
        return cached

    if settings.virustotal_api_key:
        try:
            vt_raw = await vt.lookup_ip(ip)
            stats = vt.extract_stats(vt_raw)
            result = EnrichmentResult(
                indicator_type="ip",
                value=ip,
                is_public=True,
                source=ResultSource.live,
                provider="virustotal",
                provider_status=ProviderStatus.live,
                virustotal=VirusTotalSummary(**stats) if stats else None,
                geo=_extract_vt_geo(vt_raw),
                raw={"attributes_present": bool(vt_raw.get("data"))},
            )
            cache.set(cache_key, result)
            return result
        except vt.VirusTotalError as exc:
            logger.warning("VirusTotal lookup failed for ip=%s: %s", ip, exc)
            if settings.demo_mode:
                return _demo_result("ip", ip, is_public=True)
            return _provider_failure(
                indicator_type="ip", value=ip, is_public=True,
                status=_classify_provider_error(exc), message=str(exc),
            )

    if settings.demo_mode:
        return _demo_result("ip", ip, is_public=True)
    return _provider_failure(
        indicator_type="ip", value=ip, is_public=True,
        status=ProviderStatus.not_configured,
        message="VirusTotal API key is not configured",
    )


def _extract_vt_geo(vt_raw: dict) -> GeoInfo | None:
    try:
        attrs = vt_raw["data"]["attributes"]
        return GeoInfo(
            country=attrs.get("country"),
            asn=str(attrs.get("asn")) if attrs.get("asn") else None,
            org=attrs.get("as_owner"),
        )
    except (KeyError, TypeError):
        return None


async def enrich_domain(domain: str) -> EnrichmentResult:
    return await _enrich_generic(domain, "domain", vt.lookup_domain)


async def enrich_url(url: str) -> EnrichmentResult:
    return await _enrich_generic(url, "url", vt.lookup_url)


async def enrich_hash(file_hash: str) -> EnrichmentResult:
    return await _enrich_generic(file_hash, "hash", vt.lookup_file_hash)


async def _enrich_generic(value: str, indicator_type: str, vt_lookup_fn) -> EnrichmentResult:
    settings = get_settings()
    cache = get_enrichment_cache()
    cache_key = f"{indicator_type}:{value}"

    cached = cache.get(cache_key)
    if cached is not None:
        cached.source = ResultSource.cached
        cached.provider_status = ProviderStatus.cached
        return cached

    if settings.virustotal_api_key:
        try:
            vt_raw = await vt_lookup_fn(value)
            stats = vt.extract_stats(vt_raw)
            result = EnrichmentResult(
                indicator_type=indicator_type,
                value=value,
                source=ResultSource.live,
                provider="virustotal",
                provider_status=ProviderStatus.live,
                virustotal=VirusTotalSummary(**stats) if stats else None,
            )
            cache.set(cache_key, result)
            return result
        except vt.VirusTotalError as exc:
            logger.warning("VirusTotal lookup failed for %s=%s: %s", indicator_type, value, exc)
            if settings.demo_mode:
                return _demo_result(indicator_type, value)
            return _provider_failure(
                indicator_type=indicator_type, value=value,
                status=_classify_provider_error(exc), message=str(exc),
            )

    if settings.demo_mode:
        return _demo_result(indicator_type, value)
    return _provider_failure(
        indicator_type=indicator_type, value=value,
        status=ProviderStatus.not_configured,
        message="VirusTotal API key is not configured",
    )


async def enrich_indicator(indicator_type: str, value: str) -> EnrichmentResult:
    """Dispatch to the correct enrichment path based on indicator type."""
    t = indicator_type.lower()
    if t == "ip":
        return await enrich_ip(value)
    if t == "domain":
        return await enrich_domain(value)
    if t == "url":
        return await enrich_url(value)
    if t == "hash":
        return await enrich_hash(value)
    raise ValueError(f"Unsupported indicator type: {indicator_type}")


def attach_mitre_techniques(result: EnrichmentResult, alert_name: str, description: str = "") -> EnrichmentResult:
    from app.services.mitre_mapping import map_alert_to_techniques

    result.mitre_techniques = map_alert_to_techniques(alert_name, description)
    return result
