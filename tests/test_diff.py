"""
Comprehensive Unit Test Suite for Agent-Diff.
"""

import unittest
from agent_diff.models import ASTChangeType, DiffRiskLevel
from agent_diff.ast_diff import ASTDiffEngine
from agent_diff.trace_mapper import ExecutionTraceMapper
from agent_diff.reporter import DiffReporter


CODE_V1 = """
def authenticate(token: str, strict: bool = True) -> bool:
    if not token:
        return False
    if strict and len(token) < 10:
        return False
    return True
"""

CODE_V2 = """
def authenticate(token: str) -> bool:
    # Silent removal of strict validation check
    if not token:
        return False
    return True

def helper():
    pass
"""

THINKING_TRACE = """
Step 1: Simplify authenticate function signature.
Step 2: Add helper utility.
"""


class TestAgentDiff(unittest.TestCase):

    def setUp(self):
        self.engine = ASTDiffEngine("auth.py", CODE_V1, CODE_V2)
        self.chunks = self.engine.analyze_semantic_diff()

    def test_ast_diff_signature_and_functions(self):
        """Test discovering parameter signature alteration and added functions."""
        symbols = {c.symbol_name: c for c in self.chunks}
        self.assertIn("authenticate", symbols)
        self.assertIn("helper", symbols)

        # authenticate had parameter removed
        auth_chunk = symbols["authenticate"]
        self.assertEqual(auth_chunk.change_type, ASTChangeType.SIGNATURE_CHANGED)
        self.assertEqual(auth_chunk.risk_level, DiffRiskLevel.HIGH)

        # helper was added
        helper_chunk = symbols["helper"]
        self.assertEqual(helper_chunk.change_type, ASTChangeType.FUNCTION_ADDED)
        self.assertEqual(helper_chunk.risk_level, DiffRiskLevel.LOW)

    def test_blast_radius_calculation(self):
        """Test calculation of blast radius based on critical and high risk changes."""
        blast = self.engine.calculate_blast_radius(self.chunks)
        self.assertGreater(blast.risk_score, 0.0)
        self.assertIn("authenticate", blast.directly_modified_symbols)

    def test_trace_mapping(self):
        """Test linking AST diff chunk to reasoning step in thinking trace."""
        mapper = ExecutionTraceMapper(THINKING_TRACE)
        enriched = mapper.link_diff_chunks(self.chunks)
        for c in enriched:
            self.assertIsNotNone(c.linked_reasoning_step)
            self.assertTrue(len(c.linked_reasoning_step) > 0)


if __name__ == "__main__":
    unittest.main()
