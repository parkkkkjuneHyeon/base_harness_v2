# 하네스 개선 백로그

이 문서는 하네스(harness_v1)의 알려진 한계와 개선 항목을 정리한 작업 목록이다. 각 항목은
배경 설명 없이도 바로 작업에 들어갈 수 있도록 문제 → 개선안 → 대상 파일 순으로 적었다.

**작업 시작 전에 반드시 읽을 것**: `CLAUDE.md`(모드·원칙), `README.md`(전체 구조),
`.claude/decisions/`(왜 이렇게 만들었는지). 특히 원칙 2번 — "기계적으로 판정 가능한 것만
훅으로 강제하고, 해석이 필요한 건 사람/verifier에게" — 를 어기는 개선안은 기각 대상이다.

**작업 방식**: `main`은 보호 브랜치다. `harness/<주제>` 브랜치를 만들어 작업하고, 하네스
인프라 파일과 그 외 파일을 한 커밋에 섞지 말 것 (`.githooks/pre-commit`이 막는다 —
`git config core.hooksPath .githooks` 최초 1회 설정 필요). 완료한 항목은 이 파일에서 지우고,
설계 판단이 필요했던 항목은 `.claude/decisions/`에 결정 로그를 남길 것.

---

## P1 — 안전망의 구멍 (먼저 할 것)

### 1. PyYAML이 없으면 `post_write_check` 게이트가 조용히 꺼진다

- **문제**: 모든 훅이 `_manifest.py`의 `load_manifest()`로 `project.yaml`을 읽는데, PyYAML이
  설치 안 된 환경에서는 stderr 경고 한 줄 내고 빈 dict를 반환한다. `branch_guard.py`는
  기본값(`main/master/develop`)으로 동작하지만, `post_write_check.py`는 `commands.test`가
  비게 되어 **테스트/린트 게이트가 통째로 조용히 꺼진다**. 팀원이 새 머신에서 클론 직후
  작업하면 게이트 없이 진행하고 있다는 걸 눈치채기 어렵다.
- **개선안**: 훅이 조용히 통과하는 대신, PyYAML 부재 시 exit 2로 **차단**하고 설치 명령을
  안내하게 바꾼다 (게이트는 fail-closed가 맞다 — fail-open은 branch_guard처럼 기본값으로
  대체 가능한 경우에만). 또는 `/init` 절차 0단계에 `python3 -c "import yaml"` 확인을 추가한다.
- **대상**: `.claude/hooks/_manifest.py`, `.claude/hooks/post_write_check.py`,
  `.claude/commands/init.md`
- **난이도**: 하

### 2. `core.hooksPath` 미설정이면 커밋 분리 훅이 전혀 작동하지 않는다

- **문제**: `.githooks/pre-commit`은 팀원이 `git config core.hooksPath .githooks`를 직접
  실행해야만 켜진다. 깜빡하면 하네스/프로젝트 섞인 커밋이 그대로 통과한다.
  (`.claude/decisions/0008` "남은 한계"에 이미 기록됨.)
- **개선안**: `/init` 절차 0단계에 `git config core.hooksPath` 값 확인을 추가하고, 미설정이면
  설정 명령을 안내한 뒤 멈추게 한다. `/init`은 어차피 모든 프로젝트의 첫 관문이므로 여기가
  강제 지점으로 적절하다.
- **대상**: `.claude/commands/init.md`
- **난이도**: 하

### 3. `"[<task_id>]"` description 규칙이 프롬프트 지시로만 존재한다

- **문제**: 보고 누락 자동 감지(`update_board.py`)는 Agent 호출의 `description`이
  `"[<task_id>] ..."` 형식일 때만 작동한다. 오케스트레이터가 규칙을 잊으면 감지가 조용히
  꺼진다 (`.claude/decisions/0006` "남은 것"에 기록됨). 원칙 2번("규칙은 훅으로 강제한다")과
  어긋나는 상태.
- **개선안**: PreToolUse 훅(matcher: `Task`)을 추가해, `subagent_type`이
  `code-generator|impact-analyzer|verifier`인 호출의 `description`이 `^\[[A-Za-z0-9_]+\]`
  패턴이 아니면 차단하고 올바른 형식을 안내한다. 다른 타입(general-purpose 등)은 건드리지
  않는다.
- **대상**: `.claude/hooks/`에 새 훅 추가, `.claude/settings.json`에 등록
- **난이도**: 중 (Task 훅 페이로드에 `tool_input.subagent_type`/`description`이 실제로
  들어오는지 먼저 덤프해서 확인할 것 — 0006 결정 때처럼 실측 후 구현)

## P2 — 운영 비용

### 4. `post_write_check`가 Write/Edit마다 전체 테스트를 돌린다

- **문제**: 파일 하나 쓸 때마다 `commands.test` 전체가 실행된다(타임아웃 600초). 테스트가
  수십 초를 넘는 프로젝트에서는 code-generator의 파일 여러 개 작업이 기하급수로 느려진다.
- **개선안(택1)**: (a) `commands.test_fast` 필드를 매니페스트에 추가해 훅은 빠른 스모크만
  돌리고 전체 테스트는 마무리 단계에서 1회 실행, (b) 같은 run 안에서 N초 이내 연속 Write는
  마지막 것만 검사(디바운스), (c) 변경 파일 경로와 매칭되는 테스트만 선택 실행. (a)가 구현이
  가장 단순하고 예측 가능함.
- **대상**: `.claude/hooks/post_write_check.py`, `.claude/project.yaml`,
  `.claude/commands/init.md`(새 필드 안내)
- **난이도**: 중

### 5. `runs/`가 무한히 쌓인다

- **문제**: run 폴더의 아카이빙/정리 정책이 없다. 감사 기록으로 버전 관리에 포함하라고
  권장하는데, 수십 개 쌓이면 저장소가 지저분해지고 `runs/.current`만 의미 있는 상태가 된다.
- **개선안**: `runs/archive/` 규칙을 정하거나, 완료된 run을 압축 요약(summary만 남기고
  agents/ 제거)하는 정리 커맨드(`/archive-runs` 등)를 추가. 정책 판단이 필요하므로 결정
  로그를 함께 남길 것.
- **대상**: `runs/README.md`, 필요시 새 커맨드/스크립트
- **난이도**: 하~중 (정책 결정이 핵심)

### 6. 동시 세션이 `runs/.current`를 서로 덮어쓴다

- **문제**: `.current`가 전역 단일 포인터라, 두 사람(또는 두 세션)이 동시에 다른 run을
  진행하면 나중에 시작한 쪽이 포인터를 덮어쓰고, 훅(`update_board`/`approval_gate`)이 엉뚱한
  run을 기준으로 동작한다.
- **개선안**: 훅 페이로드의 `session_id`를 활용해 `runs/.current-<session_id>` 방식으로
  세션별 포인터를 분리하거나, 최소한 커맨드 문서에 "동시에 하나의 run만"이라는 제약을
  명시한다. 실측(멀티 세션 페이로드 확인) 후 결정할 것.
- **대상**: `.claude/hooks/update_board.py`, `.claude/hooks/approval_gate.py`, 커맨드 문서들
- **난이도**: 중

### 7. `pre-commit`이 분리만 하고 하네스 훅의 문법 검증은 안 한다

- **문제**: `.claude/hooks/*.py`를 고장 낸 채 커밋해도 아무도 못 잡는다. Claude Code 훅은
  실패해도 조용히 exit 0 처리되는 경로가 많아, 고장을 눈치채기 어렵다.
- **개선안**: `.githooks/pre-commit`에서 스테이징된 `.claude/hooks/*.py`가 있으면
  `python3 -m py_compile`로 문법 검사, `.claude/settings.json`이 있으면 `json.load` 검사를
  추가한다. 몇 줄이면 된다.
- **대상**: `.githooks/pre-commit`
- **난이도**: 하

## P3 — 검증·문서 부채

### 8. 서브에이전트 `model:` 프론트매터가 실제로 적용되는지 미검증

- **문제**: `code-generator`/`impact-analyzer`는 `model: haiku`로 선언되어 있지만(비용 최적화
  원칙 3번의 근거), 실제 디스패치에서 haiku로 실행되는지 한 번도 확인된 적이 없다.
- **개선안**: 실제 세션에서 각 서브에이전트를 한 번씩 디스패치하고 응답 특성/토큰 사용량으로
  모델 배정을 확인한 뒤, 결과를 결정 로그에 기록. 적용이 안 되면 `models.*` 오버라이드 경로
  (`/init` 5단계)까지 포함해 원인을 추적할 것.
- **대상**: 검증 작업 (코드 변경 없을 수 있음)
- **난이도**: 하 (작업량은 적으나 실측 필요)

### 9. 서브에이전트가 지정된 task_id를 무시하고 제멋대로 지을 수 있다

- **문제**: 실측에서 verifier가 오케스트레이터가 지정한 `t1` 대신 자기가 지은
  task_id(`dummy-hook-check`)로 보고서를 쓴 사례가 있었다 (0006 결정 로그의 검증 기록).
  보고 누락 감지가 이를 "누락"으로 잡아주긴 하지만, 애초에 안 일어나는 게 낫다.
- **개선안**: 세 에이전트 정의(`.claude/agents/*.md`)의 보고 파일 섹션에 "task_id는
  오케스트레이터가 준 값을 **그대로** 쓴다 — 더 적절해 보이는 이름이 있어도 바꾸지 않는다"를
  명시적으로 추가한다.
- **대상**: `.claude/agents/code-generator.md`, `impact-analyzer.md`, `verifier.md`
- **난이도**: 하

### 10. Windows 팀원 호환성이 검증되지 않았다

- **문제**: 훅 등록이 `python3 ...`(Windows는 보통 `python`), `.githooks/pre-commit`은
  bash 스크립트다. Windows(WSL 아닌 네이티브 git) 팀원은 훅이 아예 실행되지 않거나 에러 난다.
- **개선안**: 팀에 Windows 사용자가 있는지 먼저 확인하고, 있으면 `python3` → `python` 감지
  래퍼 또는 문서에 WSL/Git Bash 필수 명시. 없으면 README에 "macOS/Linux 전제" 한 줄만 추가.
- **대상**: `.claude/settings.json`, `.githooks/pre-commit`, `README.md`
- **난이도**: 하(문서만) ~ 중(호환 래퍼)

### 11. `CLAUDE.md`/`decisions/`/`project.yaml`의 하네스 개선분 이식이 수동이다

- **문제**: 커밋 분리 훅이 일부러 강제하지 않는 세 파일(0008 결정 참고)은, 하네스 개선
  내용을 다른 브랜치로 옮길 때 사람이 diff를 보고 프로젝트 전용 내용을 걷어내야 한다.
- **개선안**: 당장은 현상 유지가 결정 사항. 실제로 이 수동 작업이 반복되어 고통스러워지면
  그때 헬퍼 스크립트(예: 두 브랜치의 해당 파일 diff에서 하네스 성 변경만 하이라이트)를
  검토한다 — 미리 만들지 말 것.
- **대상**: (보류 — 반복 발생 시에만)
- **난이도**: 중
