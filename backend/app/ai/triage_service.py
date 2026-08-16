"""
Phase 3: structured AI triage orchestration.

Every triage call is persisted as a TriageRecord (model, prompt version,
tokens, latency, timestamp) regardless of success/failure, so the system
has a full audit trail and can be evaluated later (Phase 10).
"""
import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.groq_client import GroqUnavailableError, build_user_prompt, call_groq_triage
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.incident import Incident
from app.models.triage import TriageRecord
from app.schemas.triage import Classification, TriageResult

logger = get_logger(__name__)


def _strip_json_fences(text: str) -> str:
    """Some models wrap JSON in ```json fences despite instructions - strip defensively."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1]
        if t.endswith("```"):
            t = t.rsplit("```", 1)[0]
    return t.strip()


def _parse_and_validate(raw_text: str) -> TriageResult:
    cleaned = _strip_json_fences(raw_text)
    data = json.loads(cleaned)  # raises json.JSONDecodeError on malformed JSON
    return TriageResult.model_validate(data)  # raises ValidationError on schema mismatch


def _rule_based_fallback(incident: Incident) -> TriageResult:
    """
    Deterministic, explainable fallback used when Groq is unavailable or
    returns unparseable output. This is NOT an AI opinion - it's a simple
    severity-passthrough so the pipeline never silently drops an alert.
    """
    high_risk = incident.severity.value in ("high", "critical")
    return TriageResult(
        classification=Classification.needs_more_info,
        confidence=0.3,
        recommended_severity=incident.severity.value,
        summary=(
            "AI triage unavailable - falling back to rule-based pass-through. "
            "An analyst must manually review this incident."
        ),
        evidence=[f"Reported severity from {incident.source}: {incident.severity.value}"],
        mitre_techniques=[],
        recommended_actions=["Manual analyst review required (AI triage unavailable)"],
        requires_human_approval=True if high_risk else False,
    )


def run_triage(
    db: Session,
    incident: Incident,
    enrichment_context: list[dict] | None = None,
    runbook_excerpt: str | None = None,
) -> TriageRecord:
    settings = get_settings()

    alert_context = {
        "source": incident.source,
        "alert_name": incident.alert_name,
        "severity": incident.severity.value,
        "description": incident.description,
        "source_ip": incident.source_ip,
        "destination_ip": incident.destination_ip,
        "hostname": incident.hostname,
        "username": incident.username,
        "event_time": incident.event_time.isoformat(),
    }

    record = TriageRecord(
        incident_id=incident.id,
        model_name=settings.groq_model,
        prompt_version=settings.ai_prompt_version,
    )

    try:
        user_prompt = build_user_prompt(alert_context, enrichment_context or [], runbook_excerpt)
        response = call_groq_triage(user_prompt)

        record.raw_response = response["text"]
        record.token_usage_prompt = response.get("prompt_tokens")
        record.token_usage_completion = response.get("completion_tokens")
        record.latency_ms = response.get("latency_ms")
        record.model_name = response.get("model") or record.model_name

        result = _parse_and_validate(response["text"])
        record.result = result.model_dump(mode="json")
        record.is_fallback = False

    except GroqUnavailableError as exc:
        logger.warning("Groq unavailable for incident=%s: %s", incident.id, exc)
        result = _rule_based_fallback(incident)
        record.result = result.model_dump(mode="json")
        record.is_fallback = True
        record.error = str(exc)

    except (json.JSONDecodeError, ValidationError) as exc:
        logger.warning("Groq returned invalid/malformed triage output for incident=%s: %s", incident.id, exc)
        result = _rule_based_fallback(incident)
        record.result = result.model_dump(mode="json")
        record.is_fallback = True
        record.error = f"Invalid LLM output, rejected and repaired: {exc}"

    db.add(record)
    db.commit()
    db.refresh(record)

    from app.services.timeline_service import add_event

    classification = record.result.get("classification") if record.result else "unknown"
    add_event(
        db,
        incident.id,
        event_type="ai_triage_completed",
        description=f"AI triage completed: classification={classification}, fallback={record.is_fallback}",
        actor="ai_triage",
        metadata={"triage_record_id": record.id},
    )
    return record
