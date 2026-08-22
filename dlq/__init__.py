# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
Dead Letter Queue (DLQ) module for diagnostic persistence on catastrophic LLM exhaustion.
"""

from ufo.dlq.dead_letter_queue import DeadLetterQueue, record_dlq_event

__all__ = ["DeadLetterQueue", "record_dlq_event"]
