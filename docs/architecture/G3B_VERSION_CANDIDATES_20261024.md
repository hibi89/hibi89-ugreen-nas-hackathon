# Advance G3b — filename-based version ambiguity detection (OFFLINE/provisional)
Date: 2026-10-24 KST, ahead of 10/30-31. **No official Uliya adapter, no NAS, no file-version CLI claims.**

Module \`src/projectready/version_candidates.py\` analyzes only in-memory, authorized, complete candidate path observations from the provisional G2 \`ScanEnvelope\`. Patterns limited to versions such as \`design_v2.pdf\`, \`design-final.pdf\`, \`design_draft.pdf\` in the same exact parent directory and extension. This is **NOT** content duplicate detection, hash comparison, editor history, true last-modified chronology, semantic file identity, or proof of latest revision.

Outputs \`CANDIDATES_REVIEW\` for multiple possible versions, \`NONE_DETECTED\` for zero/one recognized candidate, \`NOT_CHECKED\` if source, authorization, scope or pagination is insufficient. \`NONE_DETECTED\` **never** means "correct/latest/safe"; the required version gate **remains NOT_CHECKED until actual supported validation**. Do not auto-select by filename lexicography or pretend file metadata is supported. Human confirmation is needed for ambiguity.

Unit tests are in \`tests/test_version_candidates.py\`. Synthetic fixtures pass a fake SDK_VERIFIED origin solely to simulate a future trusted adapter; this is not evidence of production capability.

Official SDK developer ZIP downloaded ephemerally 10/24 (SHA source in \`docs/roles/lead/G1_ZIP_METADATA_RECOVERY_20261024.md\`), but exact registered Expert Agent/CLI call and permissions remain **UNVERIFIED**. The Round 1 submission ZIP must not include these Python engineering files. Official [UGREEN Starter Kit](https://ai.ugreen.com/pages/hackathon-starter-kit) says supported capability examples do not override the specific tool package.
