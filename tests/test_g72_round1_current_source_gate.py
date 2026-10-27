"""G72: keep current FlowPilot Round1 source and release claims fail-closed."""
import json
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/submission/flowpilot_round1_qas_20261027.json"
SKILL = ROOT / "skill/flowpilot-nas/SKILL.md"
EXPECTED = "47d119123387ec46133a62fdec58ef42ca3852491b132d32798951a6430c233b"


class Round1CurrentSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.text = json.dumps(cls.data, ensure_ascii=False).lower()

    def test_exact_ten_distinct_answers(self):
        rows = self.data["questions"]
        self.assertEqual(len(rows), 10)
        self.assertEqual(len({q["question"] for q in rows}), 10)
        self.assertTrue(all(q["answer"].strip() for q in rows))
        self.assertEqual(self.data["status"], "OWNER_REVIEW_NOT_SUBMITTED")

    def test_checker_is_static_only_and_not_live_nas(self):
        self.assertIn("40505339535", self.text)
        self.assertIn("official creator", self.text)
        self.assertIn("pending", self.text)
        self.assertIn("real nas", self.text)

    def test_ai_disclosure_and_release_hold(self):
        statement = self.data["disclosure"].lower()
        self.assertIn("chatgpt", statement)
        self.assertIn("not yet", statement)
        self.assertIn("final submission", statement)

    def test_canonical_skill_byte_identity(self):
        self.assertEqual(hashlib.sha256(SKILL.read_bytes()).hexdigest(), EXPECTED)


if __name__ == "__main__":
    unittest.main()
