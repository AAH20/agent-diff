"""
Visual Terminal & Markdown Report Generator for Agent-Diff.
"""

from typing import List
from .models import AgentDiffAudit, SemanticDiffChunk, DiffRiskLevel


class DiffReporter:
    """Renders human-centric visual review summaries of autonomous AI pull requests."""

    @staticmethod
    def render_markdown(audit: AgentDiffAudit) -> str:
        md = []
        md.append(f"# 🔍 Agent-Diff Semantic PR Audit: `{audit.pr_title}`\n")
        md.append(f"> **Author Agent**: `{audit.author_agent}` | **Model**: `{audit.model_name}`")
        md.append(f"> **Verdict**: **{audit.recommendation}** | **Blast Radius Risk**: `{audit.blast_radius.risk_score}/100`\n")

        md.append("## 📊 Semantic AST Changes & Intent Overlay\n")
        md.append("| Symbol | Change Type | Risk | Semantic Intent / Discrepancy | Linked CoT Step |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")

        for c in audit.chunks:
            step_preview = (c.linked_reasoning_step[:60] + "...") if c.linked_reasoning_step else "N/A"
            md.append(f"| `{c.symbol_name}` | `{c.change_type.value}` | **{c.risk_level.value}** | {c.intent_explanation} | `{step_preview}` |")

        md.append("\n## 💥 Blast Radius Impact\n")
        md.append(f"- **Directly Modified Symbols**: {', '.join(audit.blast_radius.directly_modified_symbols) or 'None'}")
        md.append(f"- **Contract Breaking Changes**: {', '.join(audit.blast_radius.contract_breaking_changes) or 'None'}")
        md.append(f"- **Impacted Callers**: {', '.join(audit.blast_radius.impacted_callers) or 'None'}\n")

        if audit.recommendation == "BLOCK":
            md.append("> [!CAUTION]")
            md.append("> **CRITICAL REGRESSION RISK**: This PR silently removes validation guards or breaks API contracts without explicit mandate.")

        return "\n".join(md)
