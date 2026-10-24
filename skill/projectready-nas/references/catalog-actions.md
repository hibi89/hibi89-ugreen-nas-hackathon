# Public first-party Uliya catalog — read-only action declarations
Official source: UGREEN Uliya Skill Kit 0.7.3, pinned ZIP SHA-256 `cf557e5a022e4297892f39768132855154232efdedeb726b2845450ccd70e1b3`, `data/capability-catalog.json`. Source: https://ai.ugreen.com/pages/hackathon-starter-kit .

Only the specific public catalog identifiers below have been checked using ephemeral SHA-pinned metadata extraction. This is **NOT_RUN** on any real NAS, not an official Skill checker result, an Agent registration check, a license conclusion, a cloud-privacy attestation or an assertion that literal CLI flags are supported. In the official catalog the selected actions have **effect=read**, **approval=none** and **permissions.knowledgeStatus=unknown**. All require actual installed capability, user-selected scope and permission verification before any use.

## Owner-scoped Files read actions (documented catalog labels)
| Catalog action | Required keys | Optional keys relevant to this Skill |
| --- | --- | --- |
| `ug-filesystem ls` (`file-agent`) | `path`: string | `recursive`: boolean, `max-depth`: string, `limit`: string |
| `ug-filesystem find` (`file-agent`) | `path`: string | `pattern`: string, `type`: string, `min-size`: string, `max-size`: string, `date-type`: string, `start-timestamp`: string, `end-timestamp`: string, `max-depth`: string, `limit`: string |
| `ug-filesystem stat` (`file-agent`) | `path`: string | none |
| `ug-filesystem sha256sum` (`file-agent`) | `path`: string | none |
| `ug-filesystem cat` (`file-agent`) | `path`: string | `offset`: integer, `length`: integer |

File presence should default to folder-bounded listing and `stat` on exact selected paths. `sha256sum` is not a privacy or content-safety check; `cat` requires separate content authorization. Catalog `limit` does not prove complete, paginated coverage. If the actual tool does not supply verifiable full result status, treat missing files as NOT_CHECKED.

## Separately authorized Documents read actions (documented catalog labels)
| Catalog action | Required keys | Relevant optional keys |
| --- | --- | --- |
| `ug-document metadata` (`document-agent`) | none in catalog | `file`: string repeatable, `include-pages`: boolean, `directory-limit`: string |
| `ug-document qa` (`document-agent`) | `query`: string | `file`: string repeatable, `intent`, `content-scope`, `top-k`, `entities`, `answer-mode`, `evidence-mode`, `max-files`, `body-cap` (catalog mostly strings) |
| `ug-document extract` (`document-agent`) | `query`: string | `file`: string repeatable, `schema`, `content-scope`, `max-files`, `body-cap`, `dedupe`: boolean |
| `ug-document reconcile` (`document-agent`) | none in catalog | `query`: string, `file`: string repeatable, `max-files`: string |

These optional `file` fields MUST be provided with only the specific user-approved document references where the installed runtime supports them. Never search unspecified directories or widen scope because a source parameter is optional.

## Fail-closed and authorization
The public catalog labels and argument types do not prove which CLIs or Agent IDs are installed or how to invoke them: call syntax, return-field meaning, effective rights, model/cloud data flow, full listing evidence and SDK checker behavior require explicit official runtime verification. Never invoke `ug-filesystem` write/delete/rename/copy commands, `file-workflow` mutation commands, or `ug-document writing`, even if exposed by a device. No service discovery beyond the authorized folder; no uploads; no customer files or credentials in logs. If any needed result is unsupported, incomplete, unauthorized or unverifiable, report NOT_CHECKED/NEEDS_REVIEW and do not declare READY.
