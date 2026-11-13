# FlowPilot Universal — F01–F10 최종설계 85% 수용조건·증거 매트릭스

**기준일:** 2026-11-14 KST. **목표:** 사용자 확정 최종설계 F01–F10 전체의 최소 85%, 상용 출시 100%와 별개. 본 문서는 **평가용 제안·증거 추적표**이지 확정 가중치·제품 검수 승인·공식 85% 인정이 아니다. 검증 전까지 공식률 `UNASSESSED`, `[작업중]`, RELEASE HOLD.

## 산정 방식 — 2안 검토

- **A: 단순 항목 10점씩 부여.** 계산은 빠르고 무료이나 상대적으로 간단한 보고서 기능과 실제 NAS 접근·보안의 위험 차이가 무시된다. 사용자 확정 가중치가 아니므로 공식 점수에 사용할 수 없다.
- **B: 위험·고객 가치 기반 F01–F10 가중치를 사전에 승인받고, 수용조건별 CI·실기기·권리 증거가 확인된 점수만 합산.** 증거와 위험에 맞추기 쉬우나 물리 테스트와 권리 확인이 필요하다. **추천:** B를 소유자가 승인할 때만 정본으로 사용. 가중치를 85점에 맞춰 사후 조정하지 않는다.

공식 점수 계산: `최종 설계 수락한 세부조건의 사전 승인된 가중치 합 / 승인 전체 100점 ×100`. 현 시점에는 분자·분모에 적용할 **사전 확정 가중치가 없어 숫자를 생성할 수 없다.**

| 최종 ID | 최종설계 수용조건 | 검증된 항목 (합성/CI) | 실사용·상용 미검증 | 사용자 승인 가중치 |
|---|---|---|---|---|
| F01 | 권한 보유·원본 범위·로컬/SMB 명시 동의 | Tk 동의 체크, source root 제한, 무외부전송 | 실 사용자/권한 설정·UNC SMB 범위 | 미확정 |
| F02 | 독립 계약 기반 필수 납품 파일 체크리스트·템플릿 | 직접 입력+선택 SHA, 승인 후 create-only JSON, 누락 판정 | 업종별 표준 템플릿·실 고객 계약 검수 | 미확정 |
| F03 | 파일 바이트 SHA·오류·동시 변경 감지 | SHA, 읽기 전후/마지막 메타데이터 재확인, 변경은 INCOMPLETE | SMB 변경 경쟁·atomic snapshot·실장비 | 미확정 |
| F04 | 중복·버전 후보 비교·설명 | 동일 SHA/크기, 파일명 버전 후보 CI | 실제 협업 시나리오·의미상 버전 정확성 | 미확정 |
| F05 | 원본 보존·경로/권한 경계·중단 격리 | read-only, 사이즈/디렉터리 제한, 실제 Windows NTFS junction 7종 CI | 네트워크 공유 ACL/긴 경로/경합·고객 파일 | 미확정 |
| F06 | 사람이 검토 가능한 납품 보고서/이력/백업 | 한국어 PDF+JSON+HTML, SQLite 원장 SHA·백업 CI | 실 고객 PDF 대조·권리/폰트·보존 정책 | 미확정 |
| F07 | 일반 사용자 GUI·취소/재시도/복구 | Tk 실제 GUI5/OS, checkpoint metadata 재개는 NEEDS_REVIEW, 전체 재검사만 READY | 소비자 Win10/11 실 UX·신뢰 가능한 원자적 재개 | 미확정 |
| F08 | 소비자 Windows 포터블·설치/제거·검증 가능한 배포 | PyInstaller unsigned onedir EXE, ZIP SHA 검증·재배치 실행, **Windows CI 임시 설치·실행·고객파일 보존형 제거 리허설 PASS** | 실제 고객 설치 프로그램·코드서명·Win10/11 SmartScreen/Defender·라이선스/NOTICE·사용자 PC에서 설치/제거 | 미확정 |
| F09 | 실제 PC/USB·서로 다른 제조사 SMB NAS에서 읽기 전용 검수 | 호스팅 Win/Ubuntu 합성 파일과 Windows junction 테스트만 | 고객 PC·USB·사용자 승인 실 NAS 2벤더 이상 전부 미검증 | 미확정 |
| F10 | 고객 법적·상업적 수락, 지원/환불·권리 | 설계/기술/인수인계 기록만 | EULA·상업권/제3자 라이선스/판매 승인/실 고객 수락 | 미확정 |

## 형이 직접 해야 하는 작업 vs ChatGPT가 계속 할 작업

**사용자 개입 없이 진행:** F01–F08의 독립 소스·로컬 보안·GUI·Windows CI 후보 설치·제거 검증, 서명 전 사전 점검표, 모의 납품 3회 자동 재현, CI 결과·버전 관리 및 문서/해총 동기화. 무료 로컬·기존 GitHub Actions 범위를 우선 사용; 사용량 할당량은 별도.

**사용자 고유 권한이 필요한 부분:** (1) F01–F10 상대 중요도·수용기준/총 100점의 정식 승인, (2) 실기기/본인이 합법적으로 접근 가능한 Windows10/11·USB·SMB/NAS에 대한 명시적 검증 승인 또는 실증 자료 제공, (3) 고객 공개 배포·상업용 라이선스/서명/비용의 최종 결정. **사용자에게 코딩·PowerShell 실행·NAS 구매를 임의 요구하지 않는다.** 실제 NAS가 없으면 F09는 미검증으로 남긴다.

## 결과 판정

- **내부 P85 개발 게이트:** EXE/패키징/기본 CI·보안 검증의 기술 진척도만 별도 표현 가능. 공식 F01–F10 85%가 아니다.
- **공식 최종설계 85%:** 위 모든 F01–F10과 승인 가중치를 대조해 수락된 검증 증거의 합계가 85 이상일 때만 인정. 근거 미비면 `UNASSESSED` 유지.
- **상용 GO:** 실 사용자·권리·고객 보고서·설치/서명·지원 조건을 별도로 충족해야 하며 85% 수치만으로 출시 허가하지 않는다.
- **금지:** 테스트 수를 퍼센트로 환산, F09/F10 삭제, 85점에 맞춰 가중치 후조정, 고객 파일·권한을 사용자 동의 없이 전송, unsigned CI EXE를 판매물로 포장.

최근 실행 증거: [F03/F05 보안 CI #43501769821](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43501769821), [unsigned EXE ZIP 이주 #43500327639](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43500327639). **Windows 설치·제거 CI 실제 증거:** [#43504574468](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43504574468) at source SHA `f3cbfd5df1d8aa701887a1ec180df950faf03982`: `INSTALL_CANDIDATE_VERIFIED`, `INSTALLED_FILES_VERIFIED`, `INSTALLED_EXE_EXIT 0`, `UNINSTALL_SAFETY_BLOCKED` (별도 고객파일 발견), `CANDIDATE_REMOVED_NO_OTHER_FILES`, `INSTALL_REMOVE_CYCLE_PASS` 확인. [양쪽 OS 코어 CI #43504574472](https://github.com/hibi89/hibi89-ugreen-nas-hackathon/actions/runs/43504574472): Windows 102 PASS, Linux 95 PASS+7 Windows전용 SKIP, Tk5/OS·portable8 재검사/OS 성공. Windows 임시 설치 테스트는 RUNNER_TEMP 자식 폴더에서만 허용, registry/전역 PATH/외부 네트워크/고객 시스템 변경 없음. **출시용 installer가 아닌 내부 CI 리허설**임을 반드시 표시.
