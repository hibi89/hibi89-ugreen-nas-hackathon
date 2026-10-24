"""Pure tests for bounded non-content public SDK semantic index."""
import importlib.util
import io
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from sdk_semantic_index import semantic_index
from inspect_official_sdk import UnsafePackage


def fake_zip(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return output.getvalue()


class SemanticIndexTests(unittest.TestCase):
    def _index(self, docs):
        data = fake_zip(docs)
        import hashlib
        return semantic_index(data, expected_sha=hashlib.sha256(data).hexdigest())

    def test_reports_topic_lines_and_not_verified(self):
        result = self._index({"kit/README.md": "# Files Expert Agent\nUse UGOS CLI, validate and check permissions."})
        self.assertFalse(result["exact_cli_schema_verified"])
        self.assertFalse(result["license_grant_determined"])
        self.assertEqual(result["documents"][0]["topic_line_numbers"]["cli"], [2])
        self.assertIn("files expert agent", result["documents"][0]["agent_labels_mentioned_not_registry_proof"])

    def test_only_prefix_token_not_whole_command(self):
        result = self._index({"kit/README.md": "ugos validate --token PRIVATE-HIDDEN"})
        item = result["documents"][0]
        self.assertEqual(item["cli_command_prefix_candidates_not_runtime_proof"], ["ugos validate"])
        self.assertNotIn("PRIVATE-HIDDEN", str(result))

    def test_nonmatching_command_not_imagined(self):
        item = self._index({"kit/README.md": "No tool commands here."})["documents"][0]
        self.assertEqual(item["cli_command_prefix_candidates_not_runtime_proof"], [])

    def test_changed_zip_is_blocked(self):
        with self.assertRaises(UnsafePackage):
            semantic_index(fake_zip({"kit/a.md": "text"}))

    def test_path_traversal_blocked(self):
        with self.assertRaises(UnsafePackage):
            self._index({"../escape.md": "irrelevant"})

    def test_content_not_reproduced(self):
        secret = "Private-not-to-be-logged-long-passage"
        result = self._index({"kit/guide.md": "# Documents Expert Agent\n" + secret})
        self.assertNotIn(secret, str(result))

    def test_license_topic_not_legal_conclusion(self):
        result = self._index({"kit/guide.md": "License obligations apply."})
        self.assertFalse(result["license_grant_determined"])
        self.assertEqual(result["documents"][0]["topic_line_numbers"]["license"], [1])


if __name__ == "__main__":
    unittest.main()
