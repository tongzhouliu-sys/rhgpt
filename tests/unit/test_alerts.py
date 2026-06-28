"""Unit tests for src/alerts.py (C9). Runnable without FastAPI."""

import unittest

from src.alerts import AlertTracker


def _fail(etype="transient"):
    return {"type": "step_failed", "error": {"type": etype, "message": "boom"}}


def _ok():
    return {"type": "step_succeeded", "key": "s1", "provider": "p"}


class TestAlertTracker(unittest.TestCase):
    def setUp(self):
        self.fired = []
        self.t = AlertTracker(threshold=3, on_alert=lambda et, n: self.fired.append((et, n)))

    def test_fires_only_at_threshold(self):
        self.assertIsNone(self.t.observe(_fail()))
        self.assertIsNone(self.t.observe(_fail()))
        self.assertEqual(self.t.observe(_fail()), "transient")  # 3rd consecutive
        self.assertEqual(self.fired, [("transient", 3)])

    def test_keeps_firing_during_sustained_outage(self):
        for _ in range(3):
            self.t.observe(_fail())
        self.t.observe(_fail())  # 4th
        self.assertEqual(self.fired[-1], ("transient", 4))

    def test_success_resets_streak(self):
        self.t.observe(_fail())
        self.t.observe(_fail())
        self.t.observe(_ok())  # reset
        self.assertIsNone(self.t.observe(_fail()))  # count restarts at 1
        self.assertEqual(self.fired, [])

    def test_pipeline_finished_resets(self):
        self.t.observe(_fail())
        self.t.observe(_fail())
        self.t.observe({"type": "pipeline_finished"})
        self.assertIsNone(self.t.observe(_fail()))

    def test_different_type_resets_other_counter(self):
        self.t.observe(_fail("transient"))
        self.t.observe(_fail("transient"))
        # a different class appears -> transient streak should not carry over
        self.t.observe(_fail("session_expired"))
        self.assertIsNone(self.t.observe(_fail("transient")))  # transient back to 1
        self.assertEqual(self.fired, [])

    def test_fatal_counts_as_failure(self):
        self.t.observe({"type": "fatal", "error": {"type": "internal", "message": "x"}})
        self.t.observe({"type": "fatal", "error": {"type": "internal", "message": "x"}})
        self.assertEqual(
            self.t.observe({"type": "fatal", "error": {"type": "internal", "message": "x"}}),
            "internal",
        )

    def test_non_failure_events_ignored(self):
        self.assertIsNone(self.t.observe({"type": "step_started", "key": "s1"}))
        self.assertEqual(self.t.snapshot(), {})


if __name__ == "__main__":
    unittest.main()
