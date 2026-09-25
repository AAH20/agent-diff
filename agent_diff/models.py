"""
Data models and semantic schemas for Agent-Diff.
Visual AST & Execution-Trace Diffing Engine for AI Pull Requests.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import time


class ASTChangeType(str, Enum):
    FUNCTION_ADDED = "FUNCTION_ADDED"
    FUNCTION_MODIFIED = "FUNCTION_MODIFIED"
    CONTROL_FLOW_ALTERED = "CONTROL_FLOW_ALTERED"
    EDGE_CASE_DELETED = "EDGE_CASE_DELETED"
    VALIDATION_REMOVED = "VALIDATION_REMOVED"
    SIGNATURE_CHANGED = "SIGNATURE_CHANGED"
    BOILERPLATE_SLOP = "BOILERPLATE_SLOP"


class DiffRiskLevel(str, Enum):
    CRITICAL = "CRITICAL" # e.g. security or validation check deleted
    HIGH = "HIGH"         # public API contract altered
    MEDIUM = "MEDIUM"     # business logic changed
    LOW = "LOW"           # refactor or documentation addition


@dataclass
class SemanticDiffChunk:
    file_path: str
    symbol_name: str
    change_type: ASTChangeType
    risk_level: DiffRiskLevel
    original_snippet: str
    modified_snippet: str
    intent_explanation: str
    linked_reasoning_step: Optional[str] = None
    line_start: int = 1
    line_end: int = 1


@dataclass
class BlastRadiusReport:
    directly_modified_symbols: List[str] = field(default_factory=list)
    impacted_callers: List[str] = field(default_factory=list)
    contract_breaking_changes: List[str] = field(default_factory=list)
    risk_score: float = 0.0 # 0.0 to 100.0


@dataclass
class AgentDiffAudit:
    pr_title: str
    author_agent: str
    model_name: str              # e.g. "claude-opus-5-5", "gpt-6-astra", "gemini-3-8"
    files_analyzed: int
    lines_added: int
    lines_deleted: int
    chunks: List[SemanticDiffChunk] = field(default_factory=list)
    blast_radius: BlastRadiusReport = field(default_factory=BlastRadiusReport)
    ai_slop_percentage: float = 0.0
    recommendation: str = "APPROVE" # APPROVE, CAUTION, BLOCK
    timestamp: float = field(default_factory=time.time)
