"""G50 inspect the ACTUAL FlowPilot ZIP bytes, never trust filenames alone.

This only asserts archive composition and exact source parity; it cannot
certify authorship, independent licensing rights or live NAS behavior.
"""
from __future__ import annotations
import hashlib
import io
import re
import stat
import zipfile
from pathlib import Path

EXPECTED_MEMBER = 'flowpilot-nas/SKILL.md'
DANGEROUS = re.compile(r'(^|/)(?:sdk|scripts|node_modules|vendor|__pycache__|\.git)(/|$)|\.(?:py|js|mjs|exe|dll|so|wasm|sh|ps1|bat)$',re.I)


def audit_zip_bytes(raw_zip: bytes, expected_skill: bytes) -> dict:
    if not raw_zip or len(raw_zip) > 10_000_000:
        raise ValueError('Unsupported ZIP size')
    if not expected_skill or len(expected_skill) > 1_000_000:
        raise ValueError('Unsupported Skill size')
    with zipfile.ZipFile(io.BytesIO(raw_zip), 'r') as z:
        members = z.infolist()
        if len(members) != 1 or members[0].filename != EXPECTED_MEMBER:
            raise ValueError('ZIP must contain only the exact owner-authored Markdown Skill')
        item=members[0]
        if item.is_dir() or stat.S_ISLNK(item.external_attr >> 16):
            raise ValueError('ZIP directory or symbolic link not supported')
        if DANGEROUS.search(item.filename) or item.file_size > 1_000_000:
            raise ValueError('Vendor SDK, executable or overlarge content forbidden')
        if z.testzip() is not None:
            raise ValueError('Corrupted ZIP payload')
        content=z.read(item)
        if content != expected_skill:
            raise ValueError('Skill differs from pinned reviewed source')
        text=content.decode('utf-8')
        if not text.startswith('---\nname: flowpilot-nas\n'):
            raise ValueError('Missing official-compatible candidate heading')
    return {
        'status':'BYTE_COMPOSITION_PASS_NOT_LEGAL_CERTIFICATION',
        'members':[EXPECTED_MEMBER],
        'third_party_binary_members':0,
        'official_uliya_toolkit_files':0,
        'skill_sha256':hashlib.sha256(content).hexdigest(),
        'zip_sha256':hashlib.sha256(raw_zip).hexdigest(),
        'source_exact_match':True,
        'legal_rights_released':False,
        'live_nas_verified':False,
        'devpost_submitted':False,
    }
