"""
VirusTotal Public API v3 client.

Treated as a strictly non-commercial, portfolio-scale integration. Provider
failures are classified so callers never mistake synthetic data for a live
VirusTotal verdict.
"""
import asyncio

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

BASE_URL = "https://www.virustotal.com/api/v3"


class VirusTotalError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class VirusTotalRateLimitError(VirusTotalError):
    pass


class VirusTotalAuthError(VirusTotalError):
    pass


class VirusTotalNotFoundError(VirusTotalError):
    pass


class VirusTotalTimeoutError(VirusTotalError):
    pass


async def _get(path: str) -> dict:
    settings = get_settings()
    if not settings.virustotal_api_key:
        raise VirusTotalError("No VirusTotal API key configured")

    headers = {"x-apikey": settings.virustotal_api_key}
    async with httpx.AsyncClient(timeout=settings.enrichment_timeout_seconds) as client:
        for attempt in range(2):
            try:
                resp = await client.get(f"{BASE_URL}{path}", headers=headers)
                break
            except httpx.TimeoutException as exc:
                if attempt == 0:
                    await asyncio.sleep(0.2)
                    continue
                raise VirusTotalTimeoutError("VirusTotal request timed out after retry") from exc
            except httpx.RequestError as exc:
                if attempt == 0:
                    await asyncio.sleep(0.2)
                    continue
                raise VirusTotalError("VirusTotal network request failed after retry") from exc

    if resp.status_code == 429:
        raise VirusTotalRateLimitError("VirusTotal rate limit exceeded", status_code=429)
    if resp.status_code in (401, 403):
        raise VirusTotalAuthError("VirusTotal API key was rejected", status_code=resp.status_code)
    if resp.status_code == 404:
        raise VirusTotalNotFoundError("Indicator not found in VirusTotal", status_code=404)
    if resp.status_code != 200:
        raise VirusTotalError(f"VirusTotal returned HTTP {resp.status_code}", status_code=resp.status_code)

    return resp.json()


async def lookup_ip(ip: str) -> dict:
    return await _get(f"/ip_addresses/{ip}")


async def lookup_domain(domain: str) -> dict:
    return await _get(f"/domains/{domain}")


async def lookup_file_hash(file_hash: str) -> dict:
    return await _get(f"/files/{file_hash}")


async def lookup_url(url: str) -> dict:
    import base64

    url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
    return await _get(f"/urls/{url_id}")


def extract_stats(vt_response: dict) -> dict:
    """Pull the analysis-stats block out of a raw VT v3 response, defensively."""
    try:
        attrs = vt_response["data"]["attributes"]
        stats = attrs.get("last_analysis_stats", {})
        return {
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "undetected": stats.get("undetected", 0),
            "total_engines": sum(stats.values()) if stats else 0,
            "reputation": attrs.get("reputation"),
        }
    except (KeyError, TypeError):
        return {}
