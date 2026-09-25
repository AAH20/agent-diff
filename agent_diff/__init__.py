"""
Agent-Diff: Visual AST & Execution-Trace Diffing Engine for Autonomous AI PRs.
Supports Claude 3.7 Sonnet, OpenAI o3/o1, and Gemini 2.5 Pro.
"""

from .models import (
    ASTChangeType,
    DiffRiskLevel,
    SemanticDiffChunk,
    BlastRadiusReport,
    AgentDiffAudit,
)
from .ast_diff import ASTDiffEngine
from .trace_mapper import ExecutionTraceMapper
from .reporter import DiffReporter

__version__ = "1.0.0"
__all__ = [
    "ASTChangeType",
    "DiffRiskLevel",
    "SemanticDiffChunk",
    "BlastRadiusReport",
    "AgentDiffAudit",
    "ASTDiffEngine",
    "ExecutionTraceMapper",
    "DiffReporter",
]
