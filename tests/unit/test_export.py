"""Unit tests for src/export.py (C5). Stdlib-only, runnable without FastAPI."""

import io
import json
import os
import tempfile
import unittest
import zipfile

from src.export import (
    ExportError,
    build_merged_markdown,
    build_steps_zip,
    key_provider_map,
    list_step_responses,
    read_context,
)


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _make_session(d, *, with_error=False):
    _write(os.path.join(d, "01_s1_response.md"), "# s1\n\nfirst answer\n")
    _write(os.path.join(d, "02_s2_response.md"), "# s2\n\nsecond answer\n")
    ctx = {"user_question": "Q-DESIGN", "outputs": {"s1": "first", "s2": "second"}}
    _write(os.path.join(d, "context.json"), json.dumps(ctx, ensure_ascii=False))
    events = [
        {"seq": 1, "type": "step_started", "key": "s1", "provider": "ok_1"},
        {"seq": 2, "type": "step_succeeded", "key": "s1", "provider": "ok_1", "content": "x"},
        {"seq": 3, "type": "step_started", "key": "s2", "provider": "ok_2"},
        {"seq": 4, "type": "step_succeeded", "key": "s2", "provider": "ok_2", "content": "y"},
        {"seq": 5, "type": "pipeline_finished"},
    ]
    with open(os.path.join(d, "events.jsonl"), "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    if with_error:
        _write(
            os.path.join(d, "03_s3_error.json"),
            json.dumps({"type": "session_expired", "message": "login required"}),
        )


class TestExport(unittest.TestCase):
    def test_list_step_responses_ordered(self):
        with tempfile.TemporaryDirectory() as d:
            _make_session(d)
            items = list_step_responses(d)
            self.assertEqual([i[0] for i in items], [1, 2])
            self.assertEqual([i[1] for i in items], ["s1", "s2"])

    def test_key_provider_map(self):
        with tempfile.TemporaryDirectory() as d:
            _make_session(d)
            self.assertEqual(key_provider_map(d), {"s1": "ok_1", "s2": "ok_2"})

    def test_merged_markdown(self):
        with tempfile.TemporaryDirectory() as d:
            _make_session(d)
            md = build_merged_markdown(d, title="Round 1")
            self.assertIn("# Round 1", md)
            self.assertIn("Q-DESIGN", md)              # question surfaced
            self.assertIn("first answer", md)
            self.assertIn("second answer", md)
            self.assertIn("ok_1", md)                  # provider in heading
            # ordering: s1 heading appears before s2 heading
            self.assertLess(md.index("· s1"), md.index("· s2"))

    def test_merged_includes_failed_step(self):
        with tempfile.TemporaryDirectory() as d:
            _make_session(d, with_error=True)
            md = build_merged_markdown(d)
            self.assertIn("s3", md)
            self.assertIn("session_expired", md)

    def test_steps_zip_contains_files(self):
        with tempfile.TemporaryDirectory() as d:
            _make_session(d, with_error=True)
            data = build_steps_zip(d)
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names = set(zf.namelist())
                self.assertIn("01_s1_response.md", names)
                self.assertIn("02_s2_response.md", names)
                self.assertIn("03_s3_error.json", names)
                self.assertIn(b"first answer", zf.read("01_s1_response.md"))

    def test_read_context(self):
        with tempfile.TemporaryDirectory() as d:
            _make_session(d)
            ctx = read_context(d)
            self.assertEqual(ctx["user_question"], "Q-DESIGN")
            self.assertEqual(ctx["outputs"]["s2"], "second")

    def test_missing_session_raises(self):
        with self.assertRaises(ExportError):
            build_merged_markdown("/no/such/dir")

    def test_empty_session_raises(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ExportError):
                build_merged_markdown(d)
            with self.assertRaises(ExportError):
                build_steps_zip(d)

    def test_missing_context_raises(self):
        with tempfile.TemporaryDirectory() as d:
            _write(os.path.join(d, "01_s1_response.md"), "x")
            with self.assertRaises(ExportError):
                read_context(d)


if __name__ == "__main__":
    unittest.main()
