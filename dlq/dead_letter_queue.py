# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Dead Letter Queue (DLQ) implementation.
Saves diagnostic snapshots on total fallback exhaustion to disk and optionally dispatches webhook notifications.
"""

import json
import logging
import os
import threading
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """
    Diagnostic Dead Letter Queue that captures failed LLM calls after all retries and fallbacks have been exhausted.
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        snapshot_dir: Optional[str] = None,
        max_snapshots: int = 100,
        enabled: bool = True,
        webhook_url: Optional[str] = None,
    ) -> None:
        target_dir = snapshot_dir or output_dir or "logs/dlq/snapshots"
        self._output_dir = Path(target_dir)
        self._max_snapshots = max_snapshots
        self._enabled = enabled
        self._webhook_url = webhook_url or ""

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all recorded snapshots sorted by creation time."""
        snapshots = []
        if not self._output_dir.exists():
            return snapshots

        try:
            for file_path in sorted(self._output_dir.glob("*.json"), key=os.path.getmtime):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        snapshots.append(data)
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Error listing DLQ snapshots: {e}")
        return snapshots

    def _prune_oldest(self) -> None:
        """Prune oldest snapshots exceeding max_snapshots."""
        try:
            if not self._output_dir.exists():
                return
            files = sorted(self._output_dir.glob("*.json"), key=os.path.getmtime)
            if len(files) > self._max_snapshots:
                to_remove = files[: len(files) - self._max_snapshots]
                for p in to_remove:
                    try:
                        p.unlink(missing_ok=True)
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"Error pruning DLQ snapshots: {e}")

    def record_failure(
        self,
        agent_type: str,
        messages: List[Dict[str, Any]],
        error: Exception,
        model: str = "",
        circuit_breaker_state: str = "UNKNOWN",
        extra_meta: Optional[Dict[str, Any]] = None,
    ) -> Optional[Path]:
        """
        Record a failure diagnostic snapshot to disk without raising into caller.
        """
        if not self._enabled:
            return None

        try:
            self._output_dir.mkdir(parents=True, exist_ok=True)

            timestamp_str = time.strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            safe_agent = str(agent_type).replace("/", "_").replace("\\", "_")
            filename = f"{safe_agent}_{timestamp_str}_{unique_id}.json"
            snapshot_path = self._output_dir / filename

            last_user_len = 0
            if messages:
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        last_user_len = len(str(content))
                        break

            snapshot_data: Dict[str, Any] = {
                "agent_type": str(agent_type),
                "model": model,
                "timestamp": time.time(),
                "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "error": str(error),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "message_count": len(messages) if messages else 0,
                "last_user_content_length": last_user_len,
                "circuit_breaker_state": circuit_breaker_state,
            }
            if extra_meta:
                snapshot_data["meta"] = extra_meta

            with open(snapshot_path, "w", encoding="utf-8") as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
            logger.warning(f"Recorded DLQ snapshot to {snapshot_path}")

            self._prune_oldest()
            self._dispatch_webhook(snapshot_data)
            return snapshot_path
        except Exception as e:
            logger.error(f"Failed to record DLQ snapshot: {e}")
            return None

    def _dispatch_webhook(self, snapshot_data: Dict[str, Any]) -> None:
        """
        Optionally dispatch snapshot payload to configured webhook URL.
        """
        try:
            webhook_url = self._webhook_url
            if not webhook_url:
                from ufo.config.config_loader import get_ufo_config
                cfg = get_ufo_config()
                dlq_cfg = getattr(cfg.system, "dlq", None) or cfg.system.get("DLQ", {})
                if isinstance(dlq_cfg, dict):
                    webhook_url = dlq_cfg.get("WEBHOOK_URL", "")

            if webhook_url and str(webhook_url).strip():
                import urllib.request
                req = urllib.request.Request(
                    str(webhook_url).strip(),
                    data=json.dumps(snapshot_data).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=2.0) as response:
                    logger.info(f"DLQ webhook dispatched to {webhook_url}, status: {response.status}")
        except Exception as e:
            logger.debug(f"DLQ webhook dispatch skipped or failed: {e}")


_default_dlq_instance: Optional[DeadLetterQueue] = None
_dlq_lock = threading.Lock()


def get_default_dlq() -> DeadLetterQueue:
    """Lazily construct or return singleton DLQ instance using system.yaml DLQ block."""
    global _default_dlq_instance
    if _default_dlq_instance is None:
        with _dlq_lock:
            if _default_dlq_instance is None:
                enabled = True
                snapshot_dir = "logs/dlq/snapshots"
                max_snapshots = 100
                webhook_url = ""
                try:
                    from ufo.config.config_loader import get_ufo_config
                    cfg = get_ufo_config()
                    dlq_cfg = getattr(cfg.system, "dlq", None) or cfg.system.get("DLQ", {})
                    if isinstance(dlq_cfg, dict):
                        enabled = dlq_cfg.get("ENABLED", True)
                        snapshot_dir = dlq_cfg.get("SNAPSHOT_DIR", "logs/dlq/snapshots")
                        max_snapshots = dlq_cfg.get("MAX_SNAPSHOTS", 100)
                        webhook_url = dlq_cfg.get("WEBHOOK_URL", "")
                except Exception as e:
                    logger.debug(f"Failed to load DLQ config: {e}")

                _default_dlq_instance = DeadLetterQueue(
                    snapshot_dir=snapshot_dir,
                    max_snapshots=max_snapshots,
                    enabled=enabled,
                    webhook_url=webhook_url,
                )
    return _default_dlq_instance


def record_dlq_event(
    agent_type: str,
    messages: List[Dict[str, Any]],
    error: Exception,
    model: str = "",
    circuit_breaker_state: str = "UNKNOWN",
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Optional[Path]:
    """
    Convenience function to record a DLQ snapshot using the configured default DLQ instance.
    """
    try:
        return get_default_dlq().record_failure(
            agent_type=agent_type,
            messages=messages,
            error=error,
            model=model,
            circuit_breaker_state=circuit_breaker_state,
            extra_meta=extra_meta,
        )
    except Exception as e:
        logger.error(f"record_dlq_event failed: {e}")
        return None
