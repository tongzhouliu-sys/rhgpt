import os
import unittest

from src.manager import ProviderManager
from tests.fixtures.providers import ok

FIX_CFG = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "fixtures", "providers.yaml")
)
PKG = "tests.fixtures.providers"


class TestProviderManager(unittest.TestCase):
    def setUp(self):
        ok.reset()
        self.m = ProviderManager(config_path=FIX_CFG, provider_package=PKG)

    def test_resolve_merges_defaults(self):
        conf = self.m.resolve("ok_1")
        self.assertEqual(conf["site"], "ok")
        self.assertEqual(conf["profile"], "p_ok")
        self.assertEqual(conf["timeout_ms"], 5000)
        self.assertEqual(conf["retries"], 2)
        self.assertEqual(conf["retry_backoff_ms"], 1)

    def test_resolve_missing_provider_raises(self):
        with self.assertRaises(ValueError):
            self.m.resolve("nope")

    def test_run_dispatches_to_site_module(self):
        out = self.m.run("ok_1", "hello world")
        self.assertTrue(out.startswith("# ok[p_ok]"))
        self.assertEqual(len(ok.calls), 1)
        self.assertEqual(ok.calls[0][0], "p_ok")

    def test_module_cache(self):
        a = self.m._load("ok")
        b = self.m._load("ok")
        self.assertIs(a, b)


if __name__ == "__main__":
    unittest.main()
