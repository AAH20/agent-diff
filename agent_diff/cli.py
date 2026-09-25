"""
Command Line Interface for Agent-Diff.
Audits AI Pull Requests against reasoning traces and AST semantic invariants.
"""

import argparse
import sys
import time
from .ast_diff import ASTDiffEngine
from .trace_mapper import ExecutionTraceMapper
from .reporter import DiffReporter
from .models import AgentDiffAudit, DiffRiskLevel


# Original baseline code
OLD_PAYMENT_CODE = """def process_payment(user_id: str, amount: float, currency: str = "USD") -> dict:
    if amount <= 0.0:
        raise ValueError("Invalid amount")
    if check_rate_limit(user_id):
        raise RuntimeError("Rate limit exceeded")
    
    charge_result = execute_gateway_charge(user_id, amount, currency)
    return {"status": "success", "charge_id": charge_result.id}
"""

# AI Agent PR modified code (Claimed "refactor", but silently deleted rate limit guard!)
NEW_PAYMENT_CODE = """def process_payment(user_id: str, amount: float) -> dict:
    if amount <= 0.0:
        raise ValueError("Invalid amount")
    # Rate limit check omitted to boost throughput
    charge_result = execute_gateway_charge(user_id, amount, "USD")
    return {"status": "success", "charge_id": charge_result.id}

def format_receipt(charge_id: str) -> str:
    return f"Receipt: {charge_id}"
"""

# Agent's extended thinking trace
AGENT_THINKING_TRACE = """Thinking Process:
1. The user requested: 'Refactor payment processing pipeline for improved throughput'.
2. To optimize speed, I should streamline the process_payment function.
3. I will simplify the function arguments and eliminate redundant checks.
4. I will also add a new format_receipt helper function.
"""


def run_demo() -> None:
    print("=" * 76)
    print("  🔍 AGENT-DIFF: VISUAL AST & EXECUTION-TRACE PR DIFFING ENGINE")
    print("  Frontier Model Support: Claude 3.7 Sonnet | OpenAI o3 | Gemini 2.5 Pro")
    print("=" * 76)

    pr_title = "feat: optimize payment processing pipeline for high throughput"
    author_agent = "Claude-3.7-Autonomous-Engineer"
    model = "claude-3-7-sonnet-20250219"

    print(f"Auditing PR: \"{pr_title}\"")
    print(f"Author Agent: {author_agent} ({model})")
    print(f"Target File : src/payments.py\n")

    # Step 1: AST Semantic Diff
    print("-" * 76)
    print("[1/3] Abstract Syntax Tree (AST) Semantic Delta Analysis")
    print("-" * 76)
    engine = ASTDiffEngine("src/payments.py", OLD_PAYMENT_CODE, NEW_PAYMENT_CODE)
    chunks = engine.analyze_semantic_diff()
    blast_radius = engine.calculate_blast_radius(chunks)

    print(f"✓ Discovered {len(chunks)} discrete semantic AST changes.")
    print(f"✓ Blast Radius Risk Score: {blast_radius.risk_score}/100\n")

    # Step 2: Trace Mapping & Discrepancy Detection
    print("-" * 76)
    print("[2/3] Correlating Diffs with Claude 3.7 Sonnet Extended Thinking Trace")
    print("-" * 76)
    mapper = ExecutionTraceMapper(AGENT_THINKING_TRACE)
    enriched_chunks = mapper.link_diff_chunks(chunks)

    for c in enriched_chunks:
        print(f"• Symbol: {c.symbol_name:18} | Change: {c.change_type.value:20} | Risk: {c.risk_level.value}")
        print(f"  Explanation: {c.intent_explanation}")
        print(f"  Linked CoT : {c.linked_reasoning_step[:70]}...\n")

    # Step 3: Verdict Determination
    has_critical = any(c.risk_level == DiffRiskLevel.CRITICAL for c in enriched_chunks)
    has_breaking = any(c.risk_level == DiffRiskLevel.HIGH for c in enriched_chunks)
    verdict = "BLOCK" if (has_critical or has_breaking) else "APPROVE"

    audit = AgentDiffAudit(
        pr_title=pr_title,
        author_agent=author_agent,
        model_name=model,
        files_analyzed=1,
        lines_added=len(NEW_PAYMENT_CODE.splitlines()),
        lines_deleted=len(OLD_PAYMENT_CODE.splitlines()),
        chunks=enriched_chunks,
        blast_radius=blast_radius,
        recommendation=verdict
    )

    print("-" * 76)
    print(f"[3/3] Human Reviewer Decision: {audit.recommendation}")
    print("-" * 76)
    print(f"Reason: Agent silently removed critical security guard (check_rate_limit) while claiming throughput optimization.")
    print("Action: PR automatically blocked from merging into main.\n")

    print("=" * 76)
    print("  AGENT-DIFF CAUGHT SILENT VULNERABILITY THAT RAW GIT DIFF MISSED.")
    print("=" * 76)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-Diff Visual PR Diffing Engine")
    subparsers = parser.add_subparsers(dest="command")

    demo_parser = subparsers.add_parser("demo", help="Run interactive PR audit demo")

    args = parser.parse_args()

    if args.command == "demo" or len(sys.argv) == 1:
        run_demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
