"""Records every MCP tool invocation to the shared audit log table."""
import time
from contextlib import contextmanager

from app.database.session import SessionLocal
from app.mcp_server.redaction import redact_dict, redact_text
from app.models.mcp_audit import McpToolCallLog


@contextmanager
def audit_tool_call(tool_name: str, arguments: dict):
    """
    Usage:
        with audit_tool_call("check_ip_reputation", {"ip": "8.8.8.8"}) as record:
            result = do_the_thing()
            record["result_summary"] = {"malicious": 0}
    On exception, the error is captured and redacted automatically.
    """
    start = time.monotonic()
    record: dict = {"result_summary": None, "error": None, "success": True}
    try:
        yield record
    except Exception as exc:  # noqa: BLE001 - we want to audit-log any failure, then re-raise
        record["success"] = False
        record["error"] = redact_text(str(exc))
        raise
    finally:
        duration_ms = int((time.monotonic() - start) * 1000)
        db = SessionLocal()
        try:
            log = McpToolCallLog(
                tool_name=tool_name,
                arguments=redact_dict(arguments),
                result_summary=redact_dict(record["result_summary"]) if isinstance(record["result_summary"], dict) else record["result_summary"],
                success=record["success"],
                error=record["error"],
                duration_ms=duration_ms,
            )
            db.add(log)
            db.commit()
        finally:
            db.close()
