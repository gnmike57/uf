# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Unified Pydantic Response Schemas for LLM responses.
Re-exports canonical schemas from ufo.agents.processors.schemas.response_schema
using consistent snake_case field names:
(function, arguments, observation, thought, status, message, questions, current_subtask, plan, comment, result).
"""

from ufo.agents.processors.schemas.response_schema import (
    AppAgentResponse,
    EvaluationAgentResponse,
    EvaluationResponse,
    EvaluationSubscore,
    HostAgentResponse,
    SaveScreenshotConfig,
)

__all__ = [
    "HostAgentResponse",
    "AppAgentResponse",
    "SaveScreenshotConfig",
    "EvaluationAgentResponse",
    "EvaluationResponse",
    "EvaluationSubscore",
]
