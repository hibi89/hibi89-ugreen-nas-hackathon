# G6 preliminary Markdown Skill candidate (2026-10-24 KST)

**Status: OFFLINE_CANDIDATE / OFFICIAL_VALIDATOR_NOT_RUN / NAS_NOT_RUN / NOT_SUBMITTED.**

## Design comparison and approved-scope decision
A) Markdown-only read-only Files/Documents Skill candidate: free, consistent with first-party public high-level features and Round 1 Markdown packaging, small maintenance surface. B) Python adapter bundled with Skill: could give deterministic checks but not permitted in the Round 1 ZIP and cannot yet be mapped to verified Uliya CLI. **Chosen A, only as provisional offline draft.** This does not reduce the requirement for official tool validation before submitting.

## Work
- `skill/projectready-nas/SKILL.md` describes owner-authorized scope, exact file checking, complete pagination, version ambiguity, separately authorized document reading and privacy NOT_CHECKED rules.
- `skill/projectready-nas/references/decision-policy.md` is the sole directly linked Markdown reference.
- `tests/test_skill_candidate.py` adds 6 offline structural/safety assertions. These tests never invoke Uliya, NAS, PII scanning or the official creation-tool checker.
- Public sources: https://ai.ugreen.com/pages/hackathon-starter-kit §§3,5–7; https://ugreenhackathon.devpost.com/rules ; https://ugreenhackathon.devpost.com/resources .
- No official CLI names/registered Expert Agent IDs or file I/O schemas inferred. Exact tool compatibility, validator and license text remain G1 **BLOCKED**.
- Intended original target of Markdown integration 11/03–04; actual draft produced early 10/24. Official integration, SDK checker and real NAS checks are still pending. Day 10/24 already closed at 100% of its fixed deliverables; this advance is separately recorded. Actual developer time not measured, cash spend 0.

## 2026-10-24 G6 선행 결과 최종 원격 검증
- 소스 커밋 [22c75f3a](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/commit/22c75f3abd5a56a9585a0de257ccff16710d457a)에서 Markdown Skill 후보·판정 참고자료·6개 구조 테스트 및 인수인계 갱신.
- [116/116 오프라인 합성/정적 테스트 PASS](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40069126450), [16개 변경 파일 종료 동기화 PASS](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/40069126414); 두 CI 모두 위 소스 SHA를 대상으로 실제 완료 확인.
- **제품 출시/공식 Uliya SDK validator·등록 CLI·Expert Agent·NAS·PII 검사·Devpost 제출 0건/미완료**. G1 기술 규격 여전히 BLOCKED. 10/24 정식 당일 산출물 100%/남은 0h; 이 G6는 선행 완료로 별도 공시. 실측시간 미측정, 10/25 기본 1.5h+별도 예비 1.5h, 외부 의존 실제 ETA 미정.
- 이 확인은 변경 없는 다른 해커톤 저장소나 KIC/PayPal의 배포/제출 상태를 검증하지 않는다.
