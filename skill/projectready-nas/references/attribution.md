# ProjectReady NAS — Disclosures and boundaries

## AI Tools
- OpenAI ChatGPT (GPT-6): assisted original Skill workflow design, safety-focused drafting, offline tests, code generation and review. The human entrant directs the project and retains submission responsibility.

## Third-Party Components
- No third-party code, executable library, runtime or SDK archive is bundled with this Markdown-only Skill candidate.
- Intended platform dependency: UGREEN Uliya / UGOS registered Expert Agents and supported Files/Documents capabilities. Source: https://ai.ugreen.com/pages/hackathon-starter-kit . Exact CLI schemas, official SDK license text and official validator behavior remain unverified.
- Workflow and decision policy are original hackathon work; official sources are linked, not reproduced.

## Data Flow
- Inputs: owner-approved NAS folder and mandatory file paths, and optionally separately approved document content.
- Planned processing: only verified Uliya-supported read-only file/document capabilities with per-item evidence and conservative Go/No-Go reporting.
- Outbound services: none intentionally configured. The Uliya model's local-versus-cloud processing remains UNVERIFIED; never represent it as proven private or read sensitive content without approval.
- No real credentials, user files or API keys are bundled.

## Validation limitations
- The offline Python unit tests and packaging preflight do not replace the official Uliya Skill Creation Tool validator, NAS runtime tests, or security certification. Neither production use nor Devpost submission is confirmed.
