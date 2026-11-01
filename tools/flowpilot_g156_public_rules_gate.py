"""G156: additional published UGREEN Round 1 rule checks on exact private G147 bytes.

NOT the first-party Uliya check-skill.mjs, NOT NAS or rights approval.
Public source contains no private owner ZIP/PDF or vendor code.
"""
from __future__ import annotations

import argparse
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZipFile

import flowpilot_g154_owner_offline_bundle as owner


class PublicRuleRefused(ValueError):
    """Sanitized local denial; never disclose candidate excerpts or paths."""


def audit_bytes(pdf: bytes, skill_zip: bytes, manifest: bytes, *, pdf_text: bool = False) -> dict:
    # Reuse G155 exact SHA/ZIP/PDF/manifest checks before evaluating public rules.
    pair = owner.verify_bytes(pdf, skill_zip, manifest, pdf_text=pdf_text)
    with ZipFile(BytesIO(skill_zip)) as archive:
        infos = archive.infolist()
        if (not 1 <= len(infos) <= 100 or len(skill_zip) > 10_000_000
                or sum(x.file_size for x in infos) > 10_000_000
                or any(x.file_size > 1_000_000 for x in infos)
                or any(not x.filename.endswith('.md') for x in infos)):
            raise PublicRuleRefused('PUBLIC_ZIP_LIMITS')
        raw = archive.read('flowpilot-3/SKILL.md').decode('utf-8')
        refs = [archive.read(x.filename).decode('utf-8') for x in infos
                if x.filename != 'flowpilot-3/SKILL.md']
    header = re.match(r'\A---\r?\n(.*?)\r?\n---\r?\n', raw, re.S)
    if not header:
        raise PublicRuleRefused('PUBLIC_FRONTMATTER_MISSING')
    attrs = {}
    for line in header.group(1).splitlines():
        match = re.fullmatch(r'(name|description):\s*(.*)', line)
        if not match or match.group(1) in attrs:
            raise PublicRuleRefused('PUBLIC_FRONTMATTER_KEYS')
        attrs[match.group(1)] = match.group(2)
    name, description = attrs.get('name', ''), attrs.get('description', '')
    if not 2 <= len(name) <= 64 or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise PublicRuleRefused('PUBLIC_SKILL_NAME_INVALID')
    if not 1 <= len(description) <= 1024:
        raise PublicRuleRefused('PUBLIC_DESCRIPTION_INVALID')
    all_text = '\n'.join([raw] + refs)
    if re.search(r'(?m)^\s*(?:TODO|TBD|FIXME)(?:\b|\s*:)', all_text, re.I):
        raise PublicRuleRefused('PUBLIC_UNRESOLVED_MARKER')
    secret_patterns = (
        r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        r'AKIA[0-9A-Z]{16}',
        r'gh[pousr]_[0-9A-Za-z]{36,}',
        r'\bsk-[0-9A-Za-z]{24,}\b',
    )
    if any(re.search(pattern, all_text) for pattern in secret_patterns):
        raise PublicRuleRefused('PUBLIC_SECRET_PATTERN')
    lower = all_text.casefold()
    if not all(term in lower for term in (
        'hackathon-original', 'third-party', 'license', 'chatgpt',
        'rights check', 'registered',
    )):
        raise PublicRuleRefused('PUBLIC_DISCLOSURE_INCOMPLETE')
    if not any(term in lower for term in (
        'not an executed', 'not tested', 'has not run', 'not executed',
    )):
        raise PublicRuleRefused('PUBLIC_UNTESTED_DISCLOSURE_MISSING')
    return {
        'schema': 'ugreen-g156-public-rule-audit-v1',
        'status': 'EXACT_G147_PUBLIC_RULES_STRUCTURAL_CHECK_PASS_NOT_OFFICIAL',
        'frontmatter_slug_valid': True, 'description_within_1024': True,
        'zip_markdown_only_and_within_limits': True,
        'disclosure_markers_present': True,
        'pdf_text_verified': pair['pdf_text_verified'],
        'candidate_sha256': pair['skill_zip_sha256'],
        'official_checker_executed': False,
        'registered_expert_verified': False, 'nas_verified': False,
        'owner_rights_approved': False, 'devpost_submitted': False,
        'release_gate': 'HOLD', 'private_content_returned': False,
    }


def audit_folder(folder: Path, *, pdf_text: bool = False) -> dict:
    if not folder.is_dir() or folder.is_symlink():
        raise PublicRuleRefused('PUBLIC_OWNER_FOLDER_MISSING')
    return audit_bytes(owner._file(folder, owner.PDF), owner._file(folder, owner.ZIP),
                       owner._file(folder, owner.MANIFEST), pdf_text=pdf_text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='G147 published rules only; not Uliya Checker')
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--pdf-text', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = audit_folder(args.folder, pdf_text=args.pdf_text)
        code = 0
    except (PublicRuleRefused, owner.Refused, OSError, ValueError, RuntimeError, KeyError, UnicodeError):
        report = {'schema': 'ugreen-g156-public-rule-audit-v1',
                  'status': 'PUBLIC_RULES_AUDIT_REFUSED',
                  'official_checker_executed': False,
                  'release_gate': 'HOLD', 'private_content_returned': False}
        code = 2
    print(json.dumps(report, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
