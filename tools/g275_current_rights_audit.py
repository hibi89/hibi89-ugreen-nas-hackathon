"""G275: read-only, fail-closed rights/source boundary for exact G274 private Skill.

The owner inputs remain private. This never grants publication rights, a license,
NAS permission, registered-Expert access, or Devpost submission approval.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import stat
import sys
from pathlib import Path
from zipfile import ZipFile, BadZipFile

SCHEMA = 'flowpilot-g275-current-candidate-rights-audit-v1'
CANDIDATE_SHA = 'f8774f45dd78d04c0f78bb3609645c63eed85fd15a2d181e2d8e6a4d5635ec78'
KIT_SHA = 'cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3'
PREFIX = 'flowpilot-3/'
MAIN = PREFIX + 'SKILL.md'
RIGHTS = PREFIX + 'references/failure-and-disclosure.md'
NAMES = frozenset({MAIN, RIGHTS, PREFIX+'references/modes-and-evidence.md',
                   PREFIX+'references/owner-evidence-contract.md',
                   PREFIX+'references/workflow-council-and-repair.md'})
DISCLOSURE = ('Principal new work for the contest:', 'OpenAI AI assistance is disclosed',
              'The Uliya Kit is UGREEN\'s official developer resource subject to its own terms.',
              'Participant rights, final PDF/ZIP selection, external uploads, public publication')
MAX_ZIP = 10 * 1024 * 1024
MAX_MEMBER = 1024 * 1024
MAX_UNPACKED = 10 * 1024 * 1024
BANNED_SECRET = re.compile(r'(?:AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|-----BEGIN [^-]*PRIVATE KEY-----)')

class AuditRefused(ValueError):
    pass

def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def zip_markdown(data: bytes, *, expected: frozenset[str], max_files: int,
                 restrict_markdown: bool = True) -> dict[str, bytes]:
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_ZIP:
        raise AuditRefused('INVALID_OR_UNBOUNDED_ARCHIVE')
    try:
        with ZipFile(io.BytesIO(data)) as z:
            infos = z.infolist()
            names = [i.filename for i in infos]
            if len(infos) != max_files or set(names) != expected or len(set(names)) != len(names):
                raise AuditRefused('UNEXPECTED_ARCHIVE_MANIFEST')
            if sum(i.file_size for i in infos) > MAX_UNPACKED:
                raise AuditRefused('ARCHIVE_UNPACK_BUDGET_EXCEEDED')
            result = {}
            for info in infos:
                mode = info.external_attr >> 16
                if (info.is_dir() or info.flag_bits & 1 or info.file_size > MAX_MEMBER
                    or info.compress_size > MAX_ZIP or info.filename.startswith('/')
                    or '\\' in info.filename or '..' in info.filename.split('/')
                    or (stat.S_IFMT(mode) == stat.S_IFLNK)
                    or (restrict_markdown and not info.filename.endswith('.md'))):
                    raise AuditRefused('UNSAFE_ARCHIVE_ENTRY')
                content = z.read(info)
                if not content or b'\x00' in content:
                    raise AuditRefused('EMPTY_OR_BINARY_SOURCE')
                result[info.filename] = content
            if z.testzip() is not None:
                raise AuditRefused('ARCHIVE_CRC_FAILURE')
            return result
    except (BadZipFile, OSError, RuntimeError, EOFError, NotImplementedError, OverflowError) as exc:
        raise AuditRefused('UNREADABLE_ARCHIVE') from exc

def audit(candidate: bytes, kit: bytes, *, candidate_sha: str = CANDIDATE_SHA) -> dict:
    if digest(candidate) != candidate_sha:
        raise AuditRefused('CANDIDATE_SHA_MISMATCH')
    if digest(kit) != KIT_SHA:
        raise AuditRefused('VENDOR_KIT_SHA_MISMATCH')
    files = zip_markdown(candidate, expected=NAMES, max_files=5)
    try:
        markdown = {k: v.decode('utf-8') for k, v in files.items()}
    except UnicodeDecodeError as exc:
        raise AuditRefused('NON_UTF8_SOURCE') from exc
    front = re.match(r'\A---\r?\n(.*?)\r?\n---\r?\n', markdown[MAIN], re.S)
    if not front or not re.search(r'(?m)^name:\s*flowpilot-3\s*$', front.group(1)):
        raise AuditRefused('INVALID_SKILL_NAME_OR_FRONTMATTER')
    if (any(s not in markdown[RIGHTS] for s in DISCLOSURE)
        or any(BANNED_SECRET.search(text) for text in markdown.values())):
        raise AuditRefused('SOURCE_DISCLOSURE_OR_SECRET_BOUNDARY_FAIL')
    if 'No vendor script, binary, SDK source' not in markdown[RIGHTS]:
        raise AuditRefused('VENDOR_REUSE_DECLARATION_MISSING')
    if ('max-depth at most 5 and limit at most 200' not in markdown[MAIN]
        or 'including a chosen limit below 200' not in markdown[PREFIX+'references/owner-evidence-contract.md']):
        raise AuditRefused('MISSING_G274_GUARD')
    try:
        with ZipFile(io.BytesIO(kit)) as k:
            vendor = []
            infos = k.infolist()
            if len(infos) > 50:
                raise AuditRefused('UNEXPECTED_KIT_MEMBERS')
            for entry in infos:
                if entry.filename.endswith('.md') and 0 < entry.file_size < 100000:
                    vendor.append(k.read(entry))
    except (BadZipFile, RuntimeError, OSError, EOFError) as exc:
        raise AuditRefused('UNREADABLE_KIT') from exc
    if not vendor or any(b == vb for b in files.values() for vb in vendor):
        raise AuditRefused('VENDOR_MARKDOWN_WHOLE_FILE_REUSE_OR_NO_REFERENCE')
    return {
        'schema': SCHEMA, 'status': 'CURRENT_G274_SOURCE_BOUNDARY_PASS_LICENSE_NOT_CLEARED',
        'candidate_zip_sha256': digest(candidate), 'official_kit_sha256': digest(kit),
        'markdown_files': len(files), 'candidate_bytes': len(candidate),
        'vendor_whole_markdown_reused': False,
        'vendor_scripts_bundled': False,
        'authoring_disclosure_present': True,
        'owner_license_or_rights_attestation': 'NOT_APPROVED',
        'third_party_ip_non_infringement_proven': False,
        'real_registered_nas_executed': False,
        'devpost_submission': 'NOT_SUBMITTED', 'release_gate': 'HOLD',
        'product_completion_pct': 73,
        'earned_new_completion_pct_points': 0,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-zip', required=True, type=Path)
    parser.add_argument('--official-kit', required=True, type=Path)
    args = parser.parse_args()
    try:
        if not all(p.is_file() and not p.is_symlink() for p in
                   (args.candidate_zip, args.official_kit)):
            raise AuditRefused('INVALID_INPUT_FILE')
        out = audit(args.candidate_zip.read_bytes(), args.official_kit.read_bytes())
        print(json.dumps(out, ensure_ascii=True, sort_keys=True))
        return 0
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({'status': 'G275_AUDIT_REFUSED', 'code': str(exc) if isinstance(exc, AuditRefused) else 'INPUT_ERROR',
                          'release_gate': 'HOLD'}, sort_keys=True))
        return 2

if __name__ == '__main__':
    sys.exit(main())
