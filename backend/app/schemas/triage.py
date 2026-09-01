"""Phase 3: structured AI triage schemas."""
import enum
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class Classification(str, enum.Enum):
    true_positive = "true_positive"
    false_positive = "false_positive"
    benign = "benign"
    needs_more_info = "needs_more_info"


class IocVerdict(BaseModel):
    indicator: str
    verdict: str
    source: str
    malicious: int | None = None
    suspicious: int | None = None


class ResponseRecommendation(BaseModel):
    action_type: str | None = None
    target: str | None = None
    priority: str = "analyst_review"
    reason: str

    @field_validator("action_type")
    @classmethod
    def validate_action_type(cls, value: str | None) -> str | None:
        allowed = {"block_ip", "isolate_host", "disable_account"}
        if value is not None and value not in allowed:
            raise ValueError(f"action_type must be one of {allowed} or null")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        allowed = {"immediate", "high", "analyst_review"}
        if value not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return value


class TriageResult(BaseModel):
    """The strict schema every LLM triage response must conform to."""

    classification: Classification
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommended_severity: str
    summary: str = Field(..., min_length=1, max_length=2000)
    evidence: list[str] = Field(default_factory=list)
    mitre_techniques: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True
    attack_story: str | None = Field(default=None, max_length=4000)
    risk_reasoning: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    ioc_verdicts: list[IocVerdict] = Field(default_factory=list)
    recommended_response: ResponseRecommendation | None = None

    @field_validator("recommended_severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v.lower() not in allowed:
            raise ValueError(f"recommended_severity must be one of {allowed}")
        return v.lower()


class TriageRecordOut(BaseModel):
    """What we persist/return - the validated result plus run metadata."""

    model_config = {"from_attributes": True}

    id: str
    incident_id: str
    model_name: str
    prompt_version: str
    result: TriageResult | None
    is_fallback: bool
    raw_response: str | None
    error: str | None
    token_usage_prompt: int | None
    token_usage_completion: int | None
    latency_ms: int | None
    created_at: datetime
