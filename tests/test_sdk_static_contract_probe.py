"""Synthetic bounded static scanner tests; no official kit or executable run."""
import hashlib
import io
import sys
import unittest
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from sdk_static_contract_probe import static_probe, shape
from inspect_official_sdk import UnsafePackage


def sample(catalog=None, script="import path from 'node:path';"):
    catalog = catalog if catalog is not None else {"agents": [{"name": "test", "capabilities": []}]}
    paths = {
        "uliya-skill-kit/scripts/check-skill.mjs": script,
        "uliya-skill-kit/scripts/check-lib.mjs": "export const x = 1;",
        "uliya-skill-kit/data/capability-catalog.json": __import__("json").dumps(catalog),
        "uliya-skill-kit/docs/skill-development-standard.md": "# doc",
    }
    f = io.BytesIO()
    with zipfile.ZipFile(f, "w") as z:
        for path, contents in paths.items():
            z.writestr(path, contents)
    data = f.getvalue()
    return data, hashlib.sha256(data).hexdigest()


class StaticCatalogTests(unittest.TestCase):
    def test_structural_shape_not_original_strings(self):
        data, sha = sample()
        result = static_probe(data, sha)
        self.assertIn("agents", result["catalog_top_level_shape"])
        self.assertNotIn('"name": "test"', str(result))
        self.assertFalse(result["sdk_checker_executed"])

    def test_detect_network_risk(self):
        data, sha = sample(script="fetch('https://example.invalid');")
        self.assertTrue(static_probe(data,sha)["checker_source_risk_markers"]["network"])

    def test_detect_shell_risk(self):
        data, sha = sample(script="import {spawn} from 'node:child_process';")
        self.assertTrue(static_probe(data,sha)["checker_source_risk_markers"]["child_process"])

    def test_detect_dynamic_eval(self):
        data, sha = sample(script="eval('1+1')")
        self.assertTrue(static_probe(data,sha)["checker_source_risk_markers"]["dynamic_code"])

    def test_hash_mismatch_rejects(self):
        data, _ = sample()
        with self.assertRaises(UnsafePackage):
            static_probe(data)

    def test_nested_shape_bounded(self):
        result = shape({"a": {"z": {"deep": {"secret": "not revealed"}}}})
        self.assertNotIn("not revealed", str(result))


if __name__=="__main__":
    unittest.main()
