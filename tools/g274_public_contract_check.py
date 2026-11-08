"""Fail-closed offline contract check for *private* UGREEN FlowPilot ZIPs.

Read-only stdlib. Does not register an Expert, read NAS or verify real execution.
Run: python tools/g274_public_contract_check.py /path/to/private-skill.zip
"""
import argparse
import hashlib
import json
from pathlib import PurePosixPath
import sys
import stat
import zipfile

ROOT = 'flowpilot-3/'
MAIN = ROOT + 'SKILL.md'
CONTRACT = ROOT + 'references/owner-evidence-contract.md'
EXPECTED_MEMBERS = frozenset({
    MAIN, CONTRACT,
    ROOT + 'references/failure-and-disclosure.md',
    ROOT + 'references/modes-and-evidence.md',
    ROOT + 'references/workflow-council-and-repair.md',
})
MAX_ZIP_BYTES = 10_000_000
MAX_TOTAL_UNCOMPRESSED = 10_000_000
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
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_ZIP_BYTES:
        raise ValueError('private Skill archive missing or unsafe')
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            names = [m.filename for m in members]
            if len(members) != len(EXPECTED_MEMBERS) or set(names) != EXPECTED_MEMBERS:
                raise ValueError('unexpected Skill member set or duplicate')
            if sum(m.file_size for m in members) > MAX_TOTAL_UNCOMPRESSED:
                raise ValueError('Skill archive exceeds total expanded size limit')
            for member in members:
                parts = PurePosixPath(member.filename).parts
                mode = member.external_attr >> 16
                if (member.is_dir() or '..' in parts or '\\' in member.filename
                        or member.file_size > 1024 * 1024
                        or member.flag_bits & 1
                        or member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG)):
                    raise ValueError('unsafe ZIP member format, mode or size')
            # Read every reference rather than only the two guarded sections.
            # A damaged unrelated Markdown file must never pass the release gate.
            if archive.testzip() is not None:
                raise ValueError('Skill ZIP CRC failed')
            text = {name: archive.read(name).decode('utf-8') for name in EXPECTED_MEMBERS}
            for name in EXPECTED_MEMBERS - {MAIN}:
                if name.removeprefix(ROOT) not in text[MAIN]:
                    raise ValueError('unlinked Skill reference')
            for name, clauses in CHECKS.items():
                if any(clause not in text[name] for clause in clauses):
                    raise ValueError('missing G274 bounded dispatch guarantee in ' + name)
            if any(clause in '\n'.join(text.values()) for clause in BANNED):
                raise ValueError('stale unbounded dispatch instructions')
    except (OSError, UnicodeError, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
        raise ValueError('unreadable Skill ZIP or reference') from exc
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
