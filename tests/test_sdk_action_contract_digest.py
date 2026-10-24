"""Offline simulated Uliya action-contract digest, no network or official SDK execution."""
import hashlib
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from sdk_action_contract_digest import action_contracts,SELECTION
from inspect_official_sdk import UnsafePackage


def fake_catalog(missing=None, parameters=None):
    groups=[]
    for cli, names in SELECTION.items():
        actions=[{"name":n,"parameters":parameters or {"path":{"type":"string","required":True}},"effect":"read",
                  "approval":"none","permissions":["read"],"errorCodes":["NOT_FOUND"],"stability":"stable"}
                 for n in names if n!=missing]
        groups.append({"name":cli,"agent":"fake-agent","actions":actions})
    z=io.BytesIO()
    with zipfile.ZipFile(z,"w") as f:
        f.writestr("uliya-skill-kit/data/capability-catalog.json",json.dumps({"clis":groups}))
    data=z.getvalue()
    return data,hashlib.sha256(data).hexdigest()


class SelectedActionTests(unittest.TestCase):
    def test_positive_contracts_not_runtime(self):
        data,sha=fake_catalog()
        r=action_contracts(data,sha)
        self.assertEqual(r["selected_action_count"],9)
        self.assertFalse(r["registered_on_live_nas"])
        self.assertFalse(r["official_checker_executed"])

    def test_parameter_keys_visible_not_values(self):
        data,sha=fake_catalog(parameters={"secret-path":{"description":"CONFIDENTIAL"}})
        r=action_contracts(data,sha)
        self.assertIn("secret-path",r["selected_contracts"][0]["parameters_structure_only"])
        self.assertNotIn("CONFIDENTIAL",str(r))

    def test_fail_if_selected_action_missing(self):
        data,sha=fake_catalog(missing="ls")
        with self.assertRaises(UnsafePackage):action_contracts(data,sha)

    def test_fail_on_unpinned_zip(self):
        data,sha=fake_catalog()
        with self.assertRaises(UnsafePackage):action_contracts(data)

    def test_no_docs_or_payload_printed(self):
        data,sha=fake_catalog()
        r=action_contracts(data,sha)
        self.assertFalse(r["original_catalog_republished"])
        self.assertNotIn("fake_catalog",str(r))

if __name__=="__main__":unittest.main()
