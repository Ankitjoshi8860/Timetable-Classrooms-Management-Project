import os
import unittest
from unittest.mock import patch

from app import create_app
from config import get_config


class ProductionReadinessTests(unittest.TestCase):
    def test_production_requires_strong_non_placeholder_secret(self):
        with patch.dict(os.environ, {"SECRET_KEY": "replace-with-a-local-secret"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "Production requires a SECRET_KEY"):
                get_config("production")

    def test_production_disables_debug_and_uses_secure_sessions(self):
        with patch.dict(os.environ, {"SECRET_KEY": "x" * 48}, clear=False):
            config = get_config("production")
        self.assertFalse(config.DEBUG)
        self.assertTrue(config.SESSION_COOKIE_SECURE)
        self.assertTrue(config.SESSION_COOKIE_HTTPONLY)

    def test_production_app_has_generic_error_routes(self):
        with patch.dict(os.environ, {"SECRET_KEY": "x" * 48}, clear=False):
            app = create_app("production")
        client = app.test_client()
        self.assertEqual(client.get("/missing-page").status_code, 404)
        self.assertIn(b"Page not found", client.get("/missing-page").data)


if __name__ == "__main__":
    unittest.main()
