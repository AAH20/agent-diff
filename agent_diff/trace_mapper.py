"""
Execution-Trace and Intent Mapper for Agent-Diff.
Maps AST code diff chunks back to the agent's extended reasoning tokens / thinking steps.
"""

from typing import List, Dict, Optional
from .models import SemanticDiffChunk, DiffRiskLevel, ASTChangeType


class ExecutionTraceMapper:
    """Correlates agent reasoning traces (Claude 3.7 Sonnet / o3) with physical code diffs."""

    def __init__(self, reasoning_trace: str):
        self.reasoning_trace = reasoning_trace
        self.trace_steps = self._parse_trace_steps(reasoning_trace)

    def _parse_trace_steps(self, trace: str) -> List[str]:
        """Extract discrete logical steps from thinking trace."""
        lines = trace.splitlines()
        steps = []
        current_step = []

        for line in lines:
            line_str = line.strip()
            if line_str.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "Step")):
                if current_step:
                    steps.append(" ".join(current_step))
                    current_step = []
                current_step.append(line_str)
            elif current_step:
                current_step.append(line_str)

        if current_step:
            steps.append(" ".join(current_step))

        return steps or [trace]

    def link_diff_chunks(self, chunks: List[SemanticDiffChunk]) -> List[SemanticDiffChunk]:
        """Match each AST diff chunk to the most relevant step in the reasoning trace."""
        for chunk in chunks:
            symbol = chunk.symbol_name.lower()
            matched_step = None

            for step in self.trace_steps:
                if symbol in step.lower() or chunk.file_path.lower() in step.lower():
                    matched_step = step
                    break

            if matched_step:
                chunk.linked_reasoning_step = matched_step
            else:
                chunk.linked_reasoning_step = "No explicit reasoning step mentioned for this change."

            # Discrepancy detector: if validation was removed but trace claimed performance optimization
            if chunk.change_type == ASTChangeType.VALIDATION_REMOVED:
                if "speed" in self.reasoning_trace.lower() or "optimize" in self.reasoning_trace.lower():
                    chunk.intent_explanation += " ⚠️ [DISCREPANCY DETECTED: Agent claimed performance optimization but deleted validation guards!]"

        return chunks
