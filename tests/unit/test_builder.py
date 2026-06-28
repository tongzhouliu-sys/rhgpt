import os
import tempfile
import unittest

from src.builder import PromptBuilder

FIX_PROMPTS = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "fixtures", "prompts")
)


class TestPromptBuilder(unittest.TestCase):
    def test_substitutes_user_question_and_step_key(self):
        b = PromptBuilder(FIX_PROMPTS)
        out = b.build("p2", {"user_question": "Q?", "outputs": {"s1": "PRIOR"}})
        self.assertIn("PRIOR", out)
        self.assertIn("Q?", out)
        self.assertNotIn("{{s1}}", out)
        self.assertNotIn("{{user_question}}", out)

    def test_leaves_spaced_and_dotted_braces_intact(self):
        # [修正-3]: legitimate {{ }} (spaced / dotted) must NOT be touched.
        b = PromptBuilder(FIX_PROMPTS)
        out = b.build("pcode", {"user_question": "Q", "outputs": {"s1": "X"}})
        self.assertIn("{{ vue_var }}", out)
        self.assertIn("{{another.expr}}", out)
        self.assertIn("X", out)  # {{s1}} still substituted

    def test_unknown_bare_placeholder_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "t.md"), "w") as f:
                f.write("keep {{unknown_bare}} as-is")
            out = PromptBuilder(d).build("t", {"user_question": "Q", "outputs": {}})
            self.assertEqual(out, "keep {{unknown_bare}} as-is")

    def test_no_reinjection_single_pass(self):
        # If a substituted value itself contains a placeholder string, it must
        # NOT be re-scanned and substituted (single regex pass).
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "t.md"), "w") as f:
                f.write("{{user_question}}")
            ctx = {"user_question": "A {{s1}} B", "outputs": {"s1": "INJECTED"}}
            out = PromptBuilder(d).build("t", ctx)
            self.assertEqual(out, "A {{s1}} B")
            self.assertNotIn("INJECTED", out)


if __name__ == "__main__":
    unittest.main()
