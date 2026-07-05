# 2차 백로그(12~20번) 작업·검토 보고서

날짜: 2026-07-05 · 작업 방식: 오케스트레이터가 code-generator 서브에이전트 7개에 병렬
위임 → 결과물 전수 검토 → 훅은 전부 실측(가짜 페이로드 + 라이브 호출)으로 검증.

## 한눈에 보기

| 항목 | 내용 | 결과 | 검증 방법 |
|---|---|---|---|
| 12 | `/create` 승인 게이트 우회 3경로 차단 | ✅ 완료 | 페이로드 시뮬레이션 + 라이브 오탐 사례 확인 |
| 13 | `post_write_check` 허용 목록(source_root+tests/) 전환 | ✅ 완료 | README/src/tests 경로별 exit code 확인 |
| 14 | `/init` 5단계 ↔ 커밋 분리 규칙 충돌 | ✅ 완료 (문서) | 문구 검토 |
| 15 | task_id 정규식 하이픈 허용 + 두 훅 상호참조 주석 | ✅ 완료 | 페이로드 + 실제 `[t-live]` 디스패치 통과 |
| 16 | `runs/.current`를 .gitignore에 | ✅ 완료 | diff 검토 |
| 17 | pre-commit에 project.yaml YAML 검증 | ✅ 완료 | bash -n + 구조 검토 |
| 18 | 최소 CI 워크플로우 | ✅ 완료 | YAML 파싱 (실제 실행은 이번 push가 첫 검증) |
| 19 | pytest exit 5 함정 | ✅ 완료 (문서) | 문구 검토 |
| 20 | 빈 `.missing.json` 잔재 삭제 | ✅ 완료 | 단위 테스트 3케이스 |

## 무엇이 바뀌었나 (중요한 것부터)

### 12. 승인 게이트가 실제로 단단해졌다 (`0014` 결정 로그)

이전에는 오케스트레이터가 ① Bash로 `touch .../APPROVED` 실행, ② `MODE` 파일을
`create`→`extend`로 Write, ③ `runs/.current` 포인터 변조 — 셋 중 아무거나로 `/create`
승인 게이트를 끌 수 있었다. 이제:

- ②③은 `approval_gate.py`가 기계적으로 차단한다 (run 상태 파일은 Write/Edit 금지 — 정상
  생성 경로가 Bash `printf`라서 정상 흐름은 안 깨짐. 페이로드 시뮬레이션으로 차단 2건·통과
  1건 확인).
- ①은 새 훅 `bash_approved_gate.py`가 휴리스틱으로 차단한다 (Bash 명령에 `APPROVED` 문자열
  포함 시 차단). **검증 중 재미있는 일**: 등록 직후 제 검증 명령 자체(주석에 APPROVED 포함)가
  이 훅에 차단당했다 — 문서화해 둔 오탐 클래스가 그대로 재현된 것이고, 훅이 라이브로
  동작한다는 증명이기도 하다. 오탐 시 명령 표현만 바꾸면 되고, 에러 메시지가 대안을 안내한다.
- **한계(정직하게)**: ①의 휴리스틱은 "APPROVED"라는 리터럴 없이 파일을 만드는 정교한 우회는
  못 잡는다. 가장 뻔한 문(create.md에 적힌 touch 명령 복붙)을 잠그는 것이 목적.

### 13. 소스 밖 파일을 써도 더 이상 테스트가 돌지 않는다

기존 제외 목록 방식은 README·IMPROVEMENTS 같은 루트 문서를 쓸 때도 전체 테스트를 돌렸고,
실제로 "pytest no tests ran(exit 5)" 게이트 실패 사고를 냈다. 이제 `project.source_root`
(기본 `src`)와 `tests/` 아래를 쓸 때만 돈다 — `0002` 결정(허용 목록이 안전)과 정합.
경로별 시뮬레이션으로 확인: `README.md`→스킵, `src/x.py`→진행, `tests/`→진행.

### 15+20. 보고 누락 감지의 잔가시 제거

- task_id에 하이픈 허용 (`[t-hotfix]` 가능) — 이전에 오케스트레이터가 `[t-verify]`로 자기
  훅에 차단당한 실사고의 재발 방지. 정규식이 두 훅에 중복 정의된 건 상호 참조 주석으로 묶음.
  실제 `[t-live]` 디스패치가 차단 없이 통과하는 것까지 라이브 확인.
- 누락이 전부 해소되면 `.missing.json`을 빈 `{}`로 남기지 않고 삭제 — 임시 디렉토리 단위
  테스트 3케이스(생성/삭제/중복 삭제)로 확인.

### 나머지

- **14, 19** (`0015` 결정 로그): 둘 다 `/init` 문서 보강으로 해결. 14는 "agents 파일 변경과
  project.yaml을 두 커밋으로 나눠라" 안내(버킷 재분류는 기각 — model 한 줄 때문에 에이전트
  정의 전체의 cherry-pick 보호를 포기하는 건 손해). 19는 "테스트 0개면 commands.test를
  비워둬라" 안내(훅에서 pytest exit 5 특별취급은 기각 — 러너별 exit code 휴리스틱은 훅을
  복잡하게 만듦).
- **16**: `runs/.current`는 머신 로컬 세션 상태라 `.gitignore`에 추가. 이미 추적 중인
  브랜치용 `git rm --cached` 안내도 `runs/README.md`에 추가.
- **17**: pre-commit이 `project.yaml` YAML 문법도 검사 (PyYAML 없으면 경고만 — pre-commit은
  보조 검사라 fail-open, 실제 게이트인 post_write_check는 fail-closed라는 구분을 주석으로
  명시).
- **18**: `.github/workflows/harness-check.yml` — push(main)/PR마다 훅 py_compile,
  settings.json/project.yaml 검증, 셸 스크립트 `bash -n`. hooksPath를 안 켠 팀원의 커밋을
  원격에서 잡는 최소 안전망.

## 남은 확인 사항 (사람이 알아야 할 것)

1. **CI의 실제 첫 실행은 이번 push다.** 로컬에서 YAML 파싱까지만 검증했으므로, push 후
   GitHub Actions 탭에서 `harness-check`가 초록불인지 한 번 확인 필요.
2. **Windows 검증은 여전히 미완** (1차 백로그 10번, `0013`) — 이번 배치와 무관하게 남아
   있는 유일한 미검증 항목. Windows 팀원 최초 사용 시 훅 동작 확인 필요.
3. **bash_approved_gate의 오탐** — 커밋 메시지나 문서에 대문자 `APPROVED`를 쓰는 Bash
   명령은 차단된다. 소문자를 쓰거나 표현을 바꾸면 된다 (이 보고서와 결정 로그도 그래서
   한글 표현을 썼다).

## 검토자 메모

7개 에이전트 결과물 중 수정 없이 그대로 수용하지 못한 것은 없었다 — 스펙을 좁게 준 덕이
크지만, 전부 diff 전수 검토와 실측 검증을 거친 뒤의 판단이다. 에이전트에게는 Bash가 없어
(code-generator 도구: Read/Write/Edit/Grep/Glob) 검증을 스스로 못 하므로, "훅 수정은
오케스트레이터가 실측 검증"이라는 분업이 이번에도 유효했다.
