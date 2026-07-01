import sys
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent / "backend"))


class ConversationFlowTests(unittest.TestCase):
    def test_chat_avoids_grammar_correction_feedback(self):
        with mock.patch("backend.main.load_models"):
            with mock.patch(
                "backend.main.generate_natural_response",
                return_value="That sounds fun! What do you usually do for fun?",
            ):
                from backend.main import app

                client = TestClient(app)
                response = client.post(
                    "/chat",
                    json={"text": "I wanna go to the park", "user_level": "intermediate"},
                )

                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body["response"], "That sounds fun! What do you usually do for fun?")
                self.assertEqual(body["grammar_check"], "")
                self.assertEqual(body["corrections"], [])
                self.assertEqual(body["slang_notes"], "")
                self.assertEqual(body["naturalness_score"], 0)


if __name__ == "__main__":
    unittest.main()
