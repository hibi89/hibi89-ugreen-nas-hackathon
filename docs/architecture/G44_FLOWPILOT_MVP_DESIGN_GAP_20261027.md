# G44 FlowPilot MVP — original design comparison, evidence proof and remaining gates

Date: 2026-10-27 KST. Branch lead/ugreen. Offline development ONLY.

## Design selection (compared)
A: generalized n8n-equivalent engine with custom runtime/scripts/REST/third-party connectors. Broader functionality but not compatible with official Markdown-only skill and registered-agent constraints, high security and time cost.
B: contest-native bounded natural-language NAS Skill with official registered experts and guarded read-only evidence. Lower cost and implementation risk; chosen for Round 1. Future generalized system remains unimplemented.

## Implemented and verified
G43: new independent FlowPilot Skill Markdown draft + deterministic natural-language slot-to-plan offline Python module and 18 written tests. GitHub workflow results not independently retrievable yet.
G44: new source src/flowpilot/evidence.py, tests/test_flowpilot_evidence.py. Local Python 3.13 verified 16/16 PASS on identical bytes. Includes positive/negative evidence, denied and truncated scans, private targets, symlink uncertainty, conflicting versions, duplicate observations and no NAS side-effects. GitHub workflow result unverified.

## Owner full vision gap
Natural-language plan exists as conservative keyword-slot rule, not full freeform LLM workflows. Real NAS reads 0. Verified Uliya expert chaining 0. Official new FlowPilot Creator/checker 0. Future SaaS integrations 0. Offline evidence report cannot prove live privacy or NAS runtime. Any 60-80 percent claim about the owner's full vision is NOT VERIFIED.

## Support reply boundary
UGREEN technical support replied on Oct 27 regarding Round 1 that no named applicable license exists for v0.7.3 kit and entrant may choose MIT, Apache-2.0 or BSD for own project. Support allows accurately stating no third-party components redistributed when true, with transparent AI tooling and official kit nonredistribution disclosures. This is a technical support communication, not a verified third-party copyright grant, official entrant signoff, or successful submission. Private sender/recipient identities and email payload deliberately excluded.

## Remaining gates and exact next actions
Verify Actions and historic G42 pending. Run newly authored FlowPilot through official UGREEN UGOS Creator and checker on its final exact SHA; do not reuse earlier ProjectReady G36 check. Author English 10-question <=500 word PDF and Markdown-only ZIP, check hash/size/attributions and have owner review. Real NAS becomes testable only in finalist official access day. Original G36/G37 source, PDF, ZIP preserved. No Devpost submission was made.

Official rules: https://ugreenhackathon.devpost.com/rules
