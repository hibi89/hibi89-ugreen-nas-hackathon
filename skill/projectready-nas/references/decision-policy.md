# Decision policy for ProjectReady NAS

| Observed condition | Check | Overall |
| --- | --- | --- |
| Exact required file returned with attributable reference from an authorized scan | PRESENT | Continue checks |
| Required file absent from a demonstrably complete, authorized listing | MISSING | BLOCKED |
| Partial scan, permission denied, unsupported tool or unverifiable reference | NOT_CHECKED | NEEDS_REVIEW |
| Restricted sensitive checklist or listing entry (`.env`, `.git`, `config.json`, keys, credentials, sessions or similar) | NOT_CHECKED (restricted; do not probe or disclose the path) | NEEDS_REVIEW |
| Multiple plausible revisions without an owner-verified final selection | VERSION_REVIEW | NEEDS_REVIEW |
| Necessary document contents not authorized or not accessible | CONTENT_NOT_CHECKED | NEEDS_REVIEW |
| Privacy or access check unsupported or without valid evidence | NOT_CHECKED | NEEDS_REVIEW |

READY is possible only when every required file is evidenced as present and all mandatory completeness, version, authorization and privacy checks have actual supported evidence. Any confirmed missing mandatory file makes the outcome BLOCKED. Other unresolved required checks make it NEEDS_REVIEW.

Output requirement ID, exact requested path, actual referenced observation, check status, limitation, and the next owner action. Do not infer unsupported device capabilities. No permission for edits or external transfer is granted.
