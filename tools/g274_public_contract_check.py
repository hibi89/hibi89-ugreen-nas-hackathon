"""Fail-closed offline contract check for *private* UGREEN FlowPilot ZIPs.

Read-only stdlib. Does not register an Expert, read NAS or verify real execution.
Run: python tools/g274_public_contract_check.py /path/to/private-skill.zip
"""
import argparse
import hashlib
import json
from pathlib import PurePosixPath
import sys
import zipfile

ROOT = 'flowpilot-3/'
MAIN = ROOT + 'SKILL.md'
CONTRACT = ROOT + 'references/owner-evidence-contract.md'
CHECKS = {
    MAIN: (
        'Never use unbounded ls',
        'max-depth at most 5 and limit at most 200',
        'Only stat exact attributable in-scope references',
        'NOT_CHECKED for absence-based claims',
    ),
    CONTRACT: (
        'The bound is reached if the returned count meets **that actual chosen limit**',
        'Do not use `ug-filesystem ls` as an initial-discovery substitute',
        'including a chosen limit below 200',
    ),
}
BANNED = ('ls, find or stat in that folder', 'if 200 entries are reached')


def inspect(path):
    """Return source digest and sizes, or raise ValueError without side effects."""
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        names = [m.filename for m in members]
        if len(members) != 5 or len(set(names)) != 5:
            raise ValueError('unexpected Skill member count or duplicate')
        for m in members:
            parts = PurePosixPath(m.filename).parts
            if (m.is_dir() or not m.filename.startswith(ROOT) or
                    '..' in parts or '\\' in m.filename or
                    not m.filename.endswith('.md') or m.file_size > 1024 * 1024):
                raise ValueError('invalid Markdown archive member')
        if MAIN not in names or CONTRACT not in names:
            raise ValueError('missing mandatory entrypoints')
        text = {n: archive.read(n).decode('utf-8') for n in CHECKS}
        for name, clauses in CHECKS.items():
            if any(s not in text[name] for s in clauses):
                raise ValueError('missing G274 bounded dispatch guarantee in ' + name)
        if any(s in '\n'.join(text.values()) for s in BANNED):
            raise ValueError('stale unbounded dispatch instructions')
    with open(path, 'rb') as source:
        sha = hashlib.file_digest(source, 'sha256').hexdigest()
    return {'archive_sha256': sha, 'markdown_members': len(members),
            'local_contract_check': 'PASS', 'registered_nas': 'NOT_RUN',
            'official_checker': 'SEPARATE_FIRST_PARTY_CHECK_REQUIRED',
            'release': 'HOLD'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('private_zip')
    args = ap.parse_args()
    try:
        print(json.dumps(inspect(args.private_zip), sort_keys=True))
    except (OSError, ValueError, UnicodeError, zipfile.BadZipFile) as e:
        print('G274_CONTRACT_FAIL: ' + str(e), file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
