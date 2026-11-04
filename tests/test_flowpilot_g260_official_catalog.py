"""G260 real Kit catalog reader: synthetic-only fixtures for public CI."""
from __future__ import annotations
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from test_sdk_parameter_matrix import fake
import flowpilot_g260_official_catalog as g260


def modify_catalog(blob: bytes, mutate):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        catalog=json.loads(z.read(g260.CATALOG))
    mutate(catalog)
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w") as z:
        z.writestr(g260.CATALOG,json.dumps(catalog))
    new=buff.getvalue()
    return new, hashlib.sha256(new).hexdigest()


class G260ExactOfficialCatalogTests(unittest.TestCase):
    def test_fixture_catalog_has_exact_nine_read_actions(self):
        blob,sha=fake()
        r=g260.matrix(blob,sha,synthetic_only=True)
        self.assertEqual(r["action_count"],9)
        self.assertFalse(r["live_nas_verified"])
        self.assertFalse(r["checker_run"])
        self.assertEqual(r["provider_calls"],0)
        self.assertEqual({x["cli"] for x in r["actions"]},
                         {"ug-filesystem","ug-document"})
        self.assertTrue(all(x["effect"]["value"]=="read" for x in r["actions"]))

    def test_official_sha_pin_cannot_be_overridden_in_production(self):
        blob,sha=fake()
        with self.assertRaises(g260.OfficialCatalogRefused):
            g260.matrix(blob,sha)
        with self.assertRaises(g260.OfficialCatalogRefused):
            g260.matrix(blob+b"x",sha,synthetic_only=True)

    def test_changing_read_action_to_write_is_refused(self):
        blob,sha=fake()
        for change in (
            lambda c:next(a for a in c["clis"][0]["actions"]
                          if a["name"]=="find").update(effect="state-change"),
            lambda c:next(a for a in c["clis"][0]["actions"]
                          if a["name"]=="find").update(approval="gateway"),
            lambda c:c["clis"][0].update(agent="shell-agent"),
        ):
            damaged,pin=modify_catalog(blob,change)
            with self.subTest(pin=pin),self.assertRaises(g260.OfficialCatalogRefused):
                g260.matrix(damaged,pin,synthetic_only=True)

    def test_duplicate_action_and_parameter_identifiers_refused(self):
        blob,sha=fake()
        changes=(
            lambda c:c["clis"][0]["actions"].append(
                dict(c["clis"][0]["actions"][0])),
            lambda c:c["clis"][0]["actions"][0]["parameters"].append(
                dict(c["clis"][0]["actions"][0]["parameters"][0])),
        )
        for change in changes:
            damaged,pin=modify_catalog(blob,change)
            with self.assertRaises(g260.OfficialCatalogRefused):
                g260.matrix(damaged,pin,synthetic_only=True)

    def test_unknown_zip_files_and_nested_traversal_refused(self):
        blob,sha=fake()
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            data=z.read(g260.CATALOG)
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:
            z.writestr(g260.CATALOG,data)
            z.writestr("../untrusted.py",b"print('no')")
        changed=buf.getvalue()
        with self.assertRaises(g260.OfficialCatalogRefused):
            g260.matrix(changed,hashlib.sha256(changed).hexdigest(),
                       synthetic_only=True)

    def test_real_kit_has_no_unapproved_bypass(self):
        self.assertEqual(len(g260.EXPECTED_SHA256),64)
        self.assertNotIn("http",str(g260.matrix.__code__.co_names))
        self.assertNotIn("subprocess",str(g260.matrix.__code__.co_names))


if __name__=="__main__":
    unittest.main()
