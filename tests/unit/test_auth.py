"""Unit tests for src/auth.py (C2). Stdlib-only, runnable without FastAPI."""

import os
import unittest

from src.auth import (
    AuthError,
    canonical_string,
    load_keystore_from_env,
    sha256_hex,
    sign,
    verify_request,
)

KEY = "client-a"
SECRET = "s3cr3t-shared-with-client-a"
KEYSTORE = {KEY: SECRET}
NOW = 1_700_000_000.0


def _sig(method, path, ts, body=b""):
    return sign(SECRET, method, path, str(ts), body)


class TestSigning(unittest.TestCase):
    def test_canonical_shape(self):
        c = canonical_string("post", "/jobs", "123", b"{}")
        self.assertEqual(
            c, "\n".join(["POST", "/jobs", "123", sha256_hex(b"{}")])
        )

    def test_roundtrip_ok_returns_key(self):
        ts = int(NOW)
        out = verify_request(
            KEYSTORE,
            "POST",
            "/jobs",
            api_key=KEY,
            timestamp=str(ts),
            signature=_sig("POST", "/jobs", ts, b'{"q":1}'),
            body=b'{"q":1}',
            now=NOW,
        )
        self.assertEqual(out, KEY)

    def test_get_empty_body(self):
        ts = int(NOW)
        out = verify_request(
            KEYSTORE,
            "GET",
            "/jobs/abc/events",
            api_key=KEY,
            timestamp=str(ts),
            signature=_sig("GET", "/jobs/abc/events", ts, b""),
            body=b"",
            now=NOW,
        )
        self.assertEqual(out, KEY)


class TestRejections(unittest.TestCase):
    def _expect(self, **over):
        ts = int(NOW)
        base = dict(
            keystore=KEYSTORE,
            method="POST",
            path="/jobs",
            api_key=KEY,
            timestamp=str(ts),
            signature=_sig("POST", "/jobs", ts, b"{}"),
            body=b"{}",
            now=NOW,
        )
        base.update(over)
        with self.assertRaises(AuthError):
            verify_request(
                base.pop("keystore"),
                base.pop("method"),
                base.pop("path"),
                **base,
            )

    def test_missing_headers(self):
        self._expect(api_key=None)
        self._expect(timestamp=None)
        self._expect(signature=None)

    def test_unknown_key(self):
        self._expect(api_key="nobody")

    def test_bad_signature(self):
        self._expect(signature="deadbeef")

    def test_body_tampering_detected(self):
        # signature computed over b"{}" but a different body is presented.
        self._expect(body=b'{"evil":true}')

    def test_timestamp_outside_window(self):
        self._expect(timestamp=str(int(NOW) - 301))

    def test_non_integer_timestamp(self):
        self._expect(timestamp="not-a-number")

    def test_path_mismatch_detected(self):
        # signed for /jobs but verifying /jobs/x -> signature won't match.
        ts = int(NOW)
        with self.assertRaises(AuthError):
            verify_request(
                KEYSTORE,
                "POST",
                "/jobs/x",
                api_key=KEY,
                timestamp=str(ts),
                signature=_sig("POST", "/jobs", ts, b"{}"),
                body=b"{}",
                now=NOW,
            )


class TestKeystoreEnv(unittest.TestCase):
    def setUp(self):
        for k in ("RHCLOUD_API_KEYS", "RHCLOUD_API_KEY", "RHCLOUD_API_SECRET"):
            os.environ.pop(k, None)

    def tearDown(self):
        self.setUp()

    def test_multi_pair_form(self):
        os.environ["RHCLOUD_API_KEYS"] = "k1:s1, k2:s2"
        store = load_keystore_from_env()
        self.assertEqual(store, {"k1": "s1", "k2": "s2"})

    def test_single_pair_form(self):
        os.environ["RHCLOUD_API_KEY"] = "k1"
        os.environ["RHCLOUD_API_SECRET"] = "s1"
        self.assertEqual(load_keystore_from_env(), {"k1": "s1"})

    def test_missing_raises(self):
        with self.assertRaises(ValueError):
            load_keystore_from_env()

    def test_malformed_pair_raises(self):
        os.environ["RHCLOUD_API_KEYS"] = "no-colon-here"
        with self.assertRaises(ValueError):
            load_keystore_from_env()


if __name__ == "__main__":
    unittest.main()
