"""Import every ORM model here so Base.metadata.create_all() picks up all tables."""
from app.models.incident import Incident  # noqa: F401
from app.models.mcp_audit import McpToolCallLog  # noqa: F401
from app.models.response_proposal import ResponseProposal  # noqa: F401
from app.models.timeline import TimelineEvent  # noqa: F401
from app.models.triage import TriageRecord  # noqa: F401
from app.models.siem_connection import SiemConnection  # noqa: F401
