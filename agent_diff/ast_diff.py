"""
AST Semantic Diff Engine for Agent-Diff.
Analyzes code deltas at the Abstract Syntax Tree level to uncover intent and risks.
"""

import ast
from typing import Dict, List, Tuple, Optional, Any
from .models import (
    ASTChangeType,
    DiffRiskLevel,
    SemanticDiffChunk,
    BlastRadiusReport,
)


class ASTDiffEngine:
    """Computes semantic Abstract Syntax Tree diffs between code revisions."""

    def __init__(self, file_path: str, old_code: str, new_code: str):
        self.file_path = file_path
        self.old_code = old_code
        self.new_code = new_code
        self.old_ast = self._safe_parse(old_code)
        self.new_ast = self._safe_parse(new_code)

    def _safe_parse(self, code: str) -> Optional[ast.AST]:
        try:
            return ast.parse(code)
        except Exception:
            return None

    def analyze_semantic_diff(self) -> List[SemanticDiffChunk]:
        """Discover semantic structural changes between old and new ASTs."""
        chunks: List[SemanticDiffChunk] = []

        if not self.old_ast or not self.new_ast:
            return chunks

        old_funcs = {n.name: n for n in ast.walk(self.old_ast) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        new_funcs = {n.name: n for n in ast.walk(self.new_ast) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

        # 1. Check for Deleted or Modified Functions
        for fname, old_node in old_funcs.items():
            if fname not in new_funcs:
                chunks.append(SemanticDiffChunk(
                    file_path=self.file_path,
                    symbol_name=fname,
                    change_type=ASTChangeType.EDGE_CASE_DELETED,
                    risk_level=DiffRiskLevel.CRITICAL,
                    original_snippet=ast.unparse(old_node)[:120],
                    modified_snippet="[DELETED]",
                    intent_explanation=f"Function '{fname}' was completely removed from the module.",
                    line_start=getattr(old_node, "lineno", 1),
                    line_end=getattr(old_node, "end_lineno", 1)
                ))
            else:
                new_node = new_funcs[fname]
                old_src = ast.unparse(old_node)
                new_src = ast.unparse(new_node)

                if old_src != new_src:
                    # Deep inspect function body changes
                    chunk = self._inspect_function_modifications(fname, old_node, new_node)
                    if chunk:
                        chunks.append(chunk)

        # 2. Check for New Functions
        for fname, new_node in new_funcs.items():
            if fname not in old_funcs:
                chunks.append(SemanticDiffChunk(
                    file_path=self.file_path,
                    symbol_name=fname,
                    change_type=ASTChangeType.FUNCTION_ADDED,
                    risk_level=DiffRiskLevel.LOW,
                    original_snippet="[NEW]",
                    modified_snippet=ast.unparse(new_node)[:120],
                    intent_explanation=f"New function '{fname}' introduced by agent.",
                    line_start=getattr(new_node, "lineno", 1),
                    line_end=getattr(new_node, "end_lineno", 1)
                ))

        return chunks

    def _inspect_function_modifications(
        self,
        fname: str,
        old_node: ast.FunctionDef,
        new_node: ast.FunctionDef
    ) -> Optional[SemanticDiffChunk]:
        """Examine changes in arguments, conditionals, and validation checks."""
        # 1. Check parameter signature changes
        old_args = [a.arg for a in old_node.args.args]
        new_args = [a.arg for a in new_node.args.args]
        if old_args != new_args:
            return SemanticDiffChunk(
                file_path=self.file_path,
                symbol_name=fname,
                change_type=ASTChangeType.SIGNATURE_CHANGED,
                risk_level=DiffRiskLevel.HIGH,
                original_snippet=f"def {fname}({', '.join(old_args)})",
                modified_snippet=f"def {fname}({', '.join(new_args)})",
                intent_explanation=f"Function signature modified: parameters changed from {old_args} to {new_args}.",
                line_start=getattr(new_node, "lineno", 1),
                line_end=getattr(new_node, "end_lineno", 1)
            )

        # 2. Check for removed validations (e.g. fewer If conditionals or raise statements)
        old_ifs = len([n for n in ast.walk(old_node) if isinstance(n, ast.If)])
        new_ifs = len([n for n in ast.walk(new_node) if isinstance(n, ast.If)])
        if new_ifs < old_ifs:
            return SemanticDiffChunk(
                file_path=self.file_path,
                symbol_name=fname,
                change_type=ASTChangeType.VALIDATION_REMOVED,
                risk_level=DiffRiskLevel.CRITICAL,
                original_snippet=ast.unparse(old_node)[:140],
                modified_snippet=ast.unparse(new_node)[:140],
                intent_explanation=f"Conditional validation guards reduced from {old_ifs} to {new_ifs}. Potential security/rate-limit bypass!",
                line_start=getattr(new_node, "lineno", 1),
                line_end=getattr(new_node, "end_lineno", 1)
            )

        # 3. Standard modification
        return SemanticDiffChunk(
            file_path=self.file_path,
            symbol_name=fname,
            change_type=ASTChangeType.FUNCTION_MODIFIED,
            risk_level=DiffRiskLevel.MEDIUM,
            original_snippet=ast.unparse(old_node)[:120],
            modified_snippet=ast.unparse(new_node)[:120],
            intent_explanation=f"Internal logic of '{fname}' modified.",
            line_start=getattr(new_node, "lineno", 1),
            line_end=getattr(new_node, "end_lineno", 1)
        )

    def calculate_blast_radius(self, chunks: List[SemanticDiffChunk]) -> BlastRadiusReport:
        """Compute system impact score based on changed symbols."""
        modified_symbols = [c.symbol_name for c in chunks]
        critical_changes = [c.symbol_name for c in chunks if c.risk_level == DiffRiskLevel.CRITICAL]

        risk_score = min(100.0, len(critical_changes) * 45.0 + len(chunks) * 10.0)

        return BlastRadiusReport(
            directly_modified_symbols=modified_symbols,
            impacted_callers=[f"{s}_handler" for s in modified_symbols],
            contract_breaking_changes=critical_changes,
            risk_score=risk_score
        )
