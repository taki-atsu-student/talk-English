import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class ApiProviderTests(unittest.TestCase):
    def test_cloud_backend_is_enabled_with_groq_key(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key", "USE_CLOUD_LLM": "true"}, clear=False):
            import backend.main as main
            importlib.reload(main)
            self.assertTrue(main.should_use_cloud_llm())
            self.assertEqual(main.GROQ_API_KEY, "test-key")


if __name__ == "__main__":
    unittest.main()
