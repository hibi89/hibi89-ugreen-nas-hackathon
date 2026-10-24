"""No real archive downloaded or executed in unit tests."""
import io
import json
import hashlib
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from sdk_catalog_digest import catalog_digest,short
from inspect_official_sdk import UnsafePackage

def fake(catalog):
    buff=io.BytesIO()
    with zipfile.ZipFile(buff,"w") as z:
        z.writestr("uliya-skill-kit/data/capability-catalog.json",json.dumps(catalog))
    blob=buff.getvalue()
    return blob,hashlib.sha256(blob).hexdigest()


class CatalogDigestTests(unittest.TestCase):
    def test_extract_identifiers_only(self):
        data,sha=fake({"clis":[{"name":"files","domain":"file","agent":"file-expert","actions":[{"name":"find","description":"SECRET_SOURCE_NOT_FOR_LOG"}]}],"invocation":{"command":"ugos cli","resultEnvelope":{"success":{"status":True}}}})
        result=catalog_digest(data,sha)
        self.assertEqual(result["catalog_entries"],1)
        self.assertEqual(result["cli_catalog_identifiers_not_runtime_verified"][0]["actions"][0]["name"],"find")
        self.assertNotIn("SECRET_SOURCE_NOT_FOR_LOG",str(result))
        self.assertFalse(result["official_checker_executed"])

    def test_unsafe_literal_value_rejected(self):
        self.assertIsNone(short("$(curl http://x)"))

    def test_command_prefix_bounded(self):
        data,sha=fake({"clis":[],"invocation":{"command":"ugos cli run --token password"}})
        self.assertIsNone(catalog_digest(data,sha)["invocation_command_prefix_as_catalog_text"])

    def test_sha_pin(self):
        data,sha=fake({"clis":[]})
        with self.assertRaises(UnsafePackage):catalog_digest(data)

    def test_cli_limit_fail_closed(self):
        data,sha=fake({"clis":[{"name":"x","actions":[]} for _ in range(31)]})
        with self.assertRaises(UnsafePackage):catalog_digest(data,sha)

    def test_actions_limit_fail_closed(self):
        data,sha=fake({"clis":[{"name":"x","actions":["act"]*33}]})
        with self.assertRaises(UnsafePackage):catalog_digest(data,sha)

    def test_domains_names_only(self):
        data,sha=fake({"clis":[],"domains":[{"id":"documents","description":"PRIVATE_TEXT"}]})
        digest=catalog_digest(data,sha)
        self.assertEqual(digest["supported_domain_ids_not_runtime_proof"],["documents"])
        self.assertNotIn("PRIVATE_TEXT",str(digest))


if __name__=="__main__":unittest.main()
