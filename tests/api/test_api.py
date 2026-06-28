"""API + SSE tests for src/main.py (C10).

These exercise the contract-3 surface with a STUB runtime injected via
create_app(run_pipeline_fn=...): auth (401), validation (400), concurrency
(429), reconnectable SSE frames + Last-Event-ID replay (no loss/no dup),
polling fallback, export three modes, health, and worker-level fatal seq.

Requires FastAPI + httpx (TestClient), which are installed in CI from
requirements.txt + requirements-dev.txt. If the stack is absent (e.g. the
minimal local container), the whole module skips instead of erroring.
"""

import io
import json
import os
import tempfile
import threading
import time
import unittest
import zipfile

from src.auth import sign

try:
    from fastapi.testclient import TestClient

    from src.main import create_app

    HAVE_STACK = True
except Exception:  # noqa: BLE001
    HAVE_STACK = False

HERE = os.path.dirname(__file__)
FIX = os.path.normpath(os.path.join(HERE, "..", "fixtures"))
FIX_CFG = os.path.join(FIX, "providers.yaml")
FIX_PROMPTS = os.path.join(FIX, "prompts")
FIX_PIPELINES = os.path.join(FIX, "pipelines")
OK2 = os.path.join(FIX_PIPELINES, "ok2.yaml")
BAD_PROVIDER = os.path.join(FIX_PIPELINES, "bad_provider.yaml")

KEY = "test-key"
SECRET = "test-secret"


def _scripted_runtime(write_files=True):
    """Stand-in for run_pipeline: emits a fixed event sequence (with seq, like
    the real runtime) and optionally writes A's response/context files."""

    def stub(pipeline, user_question, session_dir, emit, **kw):
        os.makedirs(session_dir, exist_ok=True)
        emit({"seq": 1, "type": "step_started", "key": "s1", "provider": "ok_1"})
        emit({"seq": 2, "type": "step_succeeded", "key": "s1", "provider": "ok_1", "content": "# s1\n\nA1\n"})
        emit({"seq": 3, "type": "step_started", "key": "s2", "provider": "ok_2"})
        emit({"seq": 4, "type": "step_succeeded", "key": "s2", "provider": "ok_2", "content": "# s2\n\nA2\n"})
        emit({"seq": 5, "type": "pipeline_finished"})
        if write_files:
            with open(os.path.join(session_dir, "01_s1_response.md"), "w", encoding="utf-8") as f:
                f.write("# s1\n\nA1\n")
            with open(os.path.join(session_dir, "02_s2_response.md"), "w", encoding="utf-8") as f:
                f.write("# s2\n\nA2\n")
            ctx = {"user_question": user_question, "outputs": {"s1": "A1", "s2": "A2"}}
            with open(os.path.join(session_dir, "context.json"), "w", encoding="utf-8") as f:
                json.dump(ctx, f, ensure_ascii=False)
        return {"user_question": user_question, "outputs": {"s1": "A1", "s2": "A2"}}

    return stub


def _raising_runtime(pipeline, user_question, session_dir, emit, **kw):
    os.makedirs(session_dir, exist_ok=True)
    emit({"seq": 1, "type": "step_started", "key": "s1", "provider": "ok_1"})
    raise RuntimeError("kaboom")


def _blocking_runtime(release: threading.Event):
    def stub(pipeline, user_question, session_dir, emit, **kw):
        os.makedirs(session_dir, exist_ok=True)
        emit({"seq": 1, "type": "step_started", "key": "s1", "provider": "ok_1"})
        release.wait(timeout=5)
        emit({"seq": 2, "type": "pipeline_finished"})
        return {"outputs": {}}

    return stub


def _headers(method, path, body=b""):
    ts = str(int(time.time()))
    return {
        "X-Api-Key": KEY,
        "X-Timestamp": ts,
        "X-Signature": sign(SECRET, method, path, ts, body),
        "Content-Type": "application/json",
    }


@unittest.skipUnless(HAVE_STACK, "FastAPI/httpx not installed")
class ApiTestBase(unittest.TestCase):
    runtime_factory = staticmethod(_scripted_runtime)
    max_concurrent = 2

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        app = create_app(
            keystore={KEY: SECRET},
            run_pipeline_fn=self.runtime_factory(),
            providers_path=FIX_CFG,
            prompts_dir=FIX_PROMPTS,
            sessions_root=self.tmp,
            frontend_origin="https://app.example",
            max_concurrent=self.max_concurrent,
            rate_limit_per_min=1000,
        )
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def _post_job(self, pipeline=OK2, question="design a url shortener"):
        body = json.dumps({"user_question": question, "pipeline": pipeline}).encode()
        return self.client.post("/jobs", content=body, headers=_headers("POST", "/jobs", body))

    def _wait_terminal(self, job_id, timeout=5.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = self.client.get(f"/jobs/{job_id}", headers=_headers("GET", f"/jobs/{job_id}"))
            if r.status_code == 200 and r.json()["status"] in ("succeeded", "failed"):
                return r.json()
            time.sleep(0.02)
        self.fail("job did not reach terminal state in time")


class TestAuth(ApiTestBase):
    def test_health_open(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_missing_auth_401(self):
        body = b'{"user_question":"x"}'
        r = self.client.post("/jobs", content=body)  # no signature headers
        self.assertEqual(r.status_code, 401)

    def test_bad_signature_401(self):
        body = b'{"user_question":"x"}'
        h = _headers("POST", "/jobs", body)
        h["X-Signature"] = "deadbeef"
        r = self.client.post("/jobs", content=body, headers=h)
        self.assertEqual(r.status_code, 401)


class TestJobLifecycle(ApiTestBase):
    def test_create_and_poll(self):
        r = self._post_job()
        self.assertEqual(r.status_code, 200)
        job_id = r.json()["job_id"]
        data = self._wait_terminal(job_id)
        self.assertEqual(data["status"], "succeeded")
        seqs = [e["seq"] for e in data["events"]]
        self.assertEqual(seqs, [1, 2, 3, 4, 5])

    def test_validation_400(self):
        r = self._post_job(pipeline=BAD_PROVIDER)
        self.assertEqual(r.status_code, 400)

    def test_missing_question_400(self):
        body = b'{"pipeline":"x"}'
        r = self.client.post("/jobs", content=body, headers=_headers("POST", "/jobs", body))
        self.assertEqual(r.status_code, 400)

    def test_unknown_job_404(self):
        r = self.client.get("/jobs/nope", headers=_headers("GET", "/jobs/nope"))
        self.assertEqual(r.status_code, 404)


class TestSSE(ApiTestBase):
    def test_full_stream_then_done(self):
        job_id = self._post_job().json()["job_id"]
        self._wait_terminal(job_id)
        path = f"/jobs/{job_id}/events"
        r = self.client.get(path, headers=_headers("GET", path))
        self.assertEqual(r.status_code, 200)
        text = r.text
        self.assertIn("id: 1", text)
        self.assertIn("id: 5", text)
        self.assertIn("step_succeeded", text)
        self.assertIn("event: done", text)

    def test_last_event_id_replay_no_dup(self):
        job_id = self._post_job().json()["job_id"]
        self._wait_terminal(job_id)
        path = f"/jobs/{job_id}/events"
        h = _headers("GET", path)
        h["Last-Event-ID"] = "2"  # only seq > 2 must be replayed
        text = self.client.get(path, headers=h).text
        self.assertNotIn("id: 1\n", text)
        self.assertNotIn("id: 2\n", text)
        self.assertIn("id: 3", text)
        self.assertIn("id: 5", text)
        # no event id should appear more than once
        for sid in ("id: 3", "id: 4", "id: 5"):
            self.assertEqual(text.count(sid), 1)


class TestExport(ApiTestBase):
    def _ready_job(self):
        job_id = self._post_job().json()["job_id"]
        self._wait_terminal(job_id)
        return job_id

    def test_export_merged(self):
        job_id = self._ready_job()
        path = f"/jobs/{job_id}/export"
        r = self.client.get(path + "?mode=merged", headers=_headers("GET", path))
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/markdown", r.headers["content-type"])
        self.assertIn("A1", r.text)
        self.assertIn("A2", r.text)

    def test_export_json(self):
        job_id = self._ready_job()
        path = f"/jobs/{job_id}/export"
        r = self.client.get(path + "?mode=json", headers=_headers("GET", path))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["outputs"]["s1"], "A1")

    def test_export_steps_zip(self):
        job_id = self._ready_job()
        path = f"/jobs/{job_id}/export"
        r = self.client.get(path + "?mode=steps", headers=_headers("GET", path))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            self.assertIn("01_s1_response.md", zf.namelist())

    def test_export_bad_mode_400(self):
        job_id = self._ready_job()
        path = f"/jobs/{job_id}/export"
        r = self.client.get(path + "?mode=bogus", headers=_headers("GET", path))
        self.assertEqual(r.status_code, 400)


class TestFatalSeq(ApiTestBase):
    runtime_factory = staticmethod(lambda: _raising_runtime)

    def test_worker_fatal_continues_seq(self):
        job_id = self._post_job().json()["job_id"]
        data = self._wait_terminal(job_id)
        self.assertEqual(data["status"], "failed")
        events = data["events"]
        self.assertEqual(events[0]["seq"], 1)
        fatal = events[-1]
        self.assertEqual(fatal["type"], "fatal")
        self.assertEqual(fatal["seq"], 2)  # seq continues after runtime's last
        self.assertEqual(fatal["error"]["type"], "internal")


@unittest.skipUnless(HAVE_STACK, "FastAPI/httpx not installed")
class TestConcurrencyLimit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.release = threading.Event()
        app = create_app(
            keystore={KEY: SECRET},
            run_pipeline_fn=_blocking_runtime(self.release),
            providers_path=FIX_CFG,
            prompts_dir=FIX_PROMPTS,
            sessions_root=self.tmp,
            max_concurrent=1,
            rate_limit_per_min=1000,
        )
        self.client = TestClient(app)

    def tearDown(self):
        self.release.set()
        self.client.close()

    def test_max_concurrent_429(self):
        body = json.dumps({"user_question": "q", "pipeline": OK2}).encode()
        r1 = self.client.post("/jobs", content=body, headers=_headers("POST", "/jobs", body))
        self.assertEqual(r1.status_code, 200)
        # second job while the first is still occupying the single slot -> 429
        r2 = self.client.post("/jobs", content=body, headers=_headers("POST", "/jobs", body))
        self.assertEqual(r2.status_code, 429)
        self.release.set()


@unittest.skipUnless(HAVE_STACK, "FastAPI/httpx not installed")
class TestRateLimit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        app = create_app(
            keystore={KEY: SECRET},
            run_pipeline_fn=_scripted_runtime(),
            providers_path=FIX_CFG,
            prompts_dir=FIX_PROMPTS,
            sessions_root=self.tmp,
            max_concurrent=10,
            rate_limit_per_min=2,  # tiny window for the test
        )
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_rate_limit_429(self):
        body = json.dumps({"user_question": "q", "pipeline": OK2}).encode()
        codes = []
        for _ in range(3):
            r = self.client.post("/jobs", content=body, headers=_headers("POST", "/jobs", body))
            codes.append(r.status_code)
        self.assertEqual(codes[:2], [200, 200])
        self.assertEqual(codes[2], 429)  # 3rd within the same minute window


if __name__ == "__main__":
    unittest.main()
