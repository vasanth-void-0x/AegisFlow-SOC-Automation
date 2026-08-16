"""
Response action adapters.

DEMO adapters simulate the effect of a response action and always return a
clearly-labeled simulated result - no real system/network calls are made.

The REAL adapter path is intentionally left unimplemented as a hard stop:
even if someone sets ENABLE_REAL_RESPONSE_ADAPTER=true, this project will
refuse to execute a real destructive action, because building a genuine
firewall/EDR integration is outside the safe scope of a portfolio project.
This is a deliberate, documented safety boundary - not a bug.
"""
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.response_proposal import ActionType

logger = get_logger(__name__)


class RealAdapterDisabledError(Exception):
    pass


def _demo_result(action_type: ActionType, target: str) -> dict:
    return {
        "mode": "demo",
        "action_type": action_type.value,
        "target": target,
        "simulated": True,
        "message": f"[SIMULATED] {action_type.value} would be applied to '{target}'. "
        "No real firewall/EDR/IAM system was contacted.",
        "executed_at": datetime.now(timezone.utc).isoformat(),
    }


def execute_action(action_type: ActionType, target: str) -> dict:
    settings = get_settings()

    if settings.enable_real_response_adapter:
        # Deliberately unimplemented - see module docstring. This keeps the
        # project safe by construction even if the env var is flipped.
        logger.error(
            "ENABLE_REAL_RESPONSE_ADAPTER=true but no real adapter is implemented - refusing to execute %s on %s",
            action_type.value,
            target,
        )
        raise RealAdapterDisabledError(
            "Real response adapters are not implemented in this project. "
            "This is an intentional safety boundary, not a configuration error."
        )

    logger.info("Executing DEMO action: %s on %s", action_type.value, target)
    return _demo_result(action_type, target)


def execute_rollback(action_type: ActionType, target: str, original_execution_result: dict | None) -> dict:
    settings = get_settings()

    if settings.enable_real_response_adapter:
        raise RealAdapterDisabledError(
            "Real response adapters are not implemented in this project. "
            "This is an intentional safety boundary, not a configuration error."
        )

    return {
        "mode": "demo",
        "action_type": action_type.value,
        "target": target,
        "simulated": True,
        "message": f"[SIMULATED ROLLBACK] {action_type.value} on '{target}' would be reverted.",
        "rolled_back_at": datetime.now(timezone.utc).isoformat(),
        "original_execution": original_execution_result,
    }
