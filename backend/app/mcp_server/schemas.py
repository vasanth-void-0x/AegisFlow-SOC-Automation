"""Typed request/response schemas for every MCP tool - kept separate from the
tool functions so the schema surface is easy to review for a security audit."""
from pydantic import BaseModel, Field


class CheckIpReputationInput(BaseModel):
    ip: str = Field(..., description="IPv4 or IPv6 address to check")


class CheckFileHashInput(BaseModel):
    file_hash: str = Field(..., description="MD5, SHA1, or SHA256 file hash")


class SearchIncidentsInput(BaseModel):
    severity: str | None = Field(default=None, description="Filter: low|medium|high|critical")
    status: str | None = Field(default=None, description="Filter: new|triaging|pending_approval|contained|resolved|closed")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=50)


class GetIncidentInput(BaseModel):
    incident_id: str = Field(..., description="Incident ID, e.g. INC-XXXXXXXXXXXX")


class MapMitreTechniqueInput(BaseModel):
    alert_text: str = Field(..., description="Alert name and/or description to map to MITRE ATT&CK techniques")


class GetSocRunbookInput(BaseModel):
    query: str = Field(..., description="Description of the alert/scenario to find a relevant runbook for")


class CreateResponseProposalInput(BaseModel):
    incident_id: str
    action_type: str = Field(..., description="block_ip|isolate_host|disable_account|rollback")
    target: str = Field(..., description="The IP/host/account the action targets")
    justification: str = Field(..., min_length=10, max_length=2000)
    proposed_by: str = Field(default="mcp_tool")
