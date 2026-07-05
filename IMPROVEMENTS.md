# 하네스 개선 백로그

이 문서는 하네스(harness_v1)의 알려진 한계와 개선 항목을 정리한 작업 목록이다. 각 항목은
배경 설명 없이도 바로 작업에 들어갈 수 있도록 문제 → 개선안 → 대상 파일 순으로 적었다.

**작업 시작 전에 반드시 읽을 것**: `CLAUDE.md`(모드·원칙), `README.md`(전체 구조),
`.claude/decisions/`(왜 이렇게 만들었는지). 특히 원칙 2번 — "기계적으로 판정 가능한 것만
훅으로 강제하고, 해석이 필요한 건 사람/verifier에게" — 를 어기는 개선안은 기각 대상이다.

**작업 방식**: `main`은 보호 브랜치다. `harness/<주제>` 브랜치를 만들어 작업하고, 하네스
인프라 파일과 그 외 파일을 한 커밋에 섞지 말 것 (`.githooks/pre-commit`이 막는다 —
`git config core.hooksPath .githooks` 최초 1회 설정 필요). 완료한 항목은 이 파일의 맨 아래
"처리 완료" 섹션으로 옮기고, 설계 판단이 필요했던 항목은 `.claude/decisions/`에 결정 로그를
남길 것. 훅을 고치면 반드시 실제 호출로 검증할 것 (가정으로 구현하지 않는다 — `0006`/`0009`
결정 로그가 실측 방식의 예시다).

---

## P1 — 안전망의 구멍 (먼저 할 것)

### 12. `/create` 승인 게이트에 우회 경로가 3개 있다

- **문제**: `approval_gate.py`는 `Write|Edit` 매처에만 걸려 있어서(`settings.json` 확인됨),
  오케스트레이터가 다음 경로로 게이트를 무력화할 수 있다. `0003` 결정의 목표가 "프롬프트
  인젝션을 당해도 안 뚫리는 것"이었으므로 실질적인 구멍이다:
  1. **Bash로 `APPROVED` 생성** — `create.md` 4절이 사람용으로 안내하는
     `touch "runs/$(cat runs/.current)/APPROVED"`를 오케스트레이터가 Bash 도구로 직접
     실행해버릴 수 있다. 막는 건 프롬프트 지시뿐이다.
  2. **`runs/<run>/MODE` 변조** — MODE 파일은 보호 대상이 아니라서, Write/Edit로 내용을
     `create` → `extend`로 바꾸면 게이트가 그냥 꺼진다.
  3. **`runs/.current` 변조** — 포인터를 존재하지 않는(또는 extend 모드인) run으로 바꿔도
     게이트가 꺼진다.
- **개선안**:
  - 2·3번은 기계적으로 확실히 막을 수 있다: `approval_gate.py` 규칙 1에 `runs/*/MODE`와
    `runs/.current`의 Write/Edit 차단을 추가한다. **정상 생성 경로가 깨지지 않는 이유**:
    세 커맨드 문서의 "1. run 폴더 생성" 단계는 이 파일들을 Bash(`printf ... >`)로 만들지
    Write/Edit 도구로 만들지 않는다.
  - 1번은 완벽히 막을 수 없다(파일을 만드는 Bash 명령은 무한히 많다). PreToolUse `Bash`
    매처 훅을 추가해 `tool_input.command` 문자열에 `APPROVED`가 포함되면 차단하는
    휴리스틱으로 명백한 경로만 막고, 완벽하지 않다는 걸 훅 주석과 결정 로그에 명시한다.
    (이 훅은 `runs/.current`/`MODE`를 다시 쓰는 Bash 명령까지 막으려 들면 정상 run 생성이
    막히므로, APPROVED만 대상으로 한다.)
- **대상**: `.claude/hooks/approval_gate.py`, 새 Bash 훅(또는 approval_gate에 통합),
  `.claude/settings.json`, 결정 로그
- **난이도**: 중 (구현은 단순하지만, 정상 경로를 안 깨는지 실제 `/create` 흐름 시뮬레이션으로
  검증 필요)

### 13. `post_write_check`가 제외 목록 방식이라 소스 밖 파일에도 전체 테스트를 돌린다

- **문제**: `SKIP_PREFIXES = ("runs/", ".claude/", "CLAUDE.md")` 제외 목록이라, 그 외 전부
  (루트 `README.md`, `IMPROVEMENTS.md`, `.githooks/` 등)를 Write/Edit할 때마다 테스트·린트가
  전체 실행된다. **실사고**: 템플릿 브랜치에서 `README.md`를 쓰다가 pytest가
  "no tests ran"(exit 5)으로 게이트 실패를 일으켰다. `0002` 결정이 이미 "제외 목록보다 허용
  목록(source_root)이 안전하다"고 명시했는데, 이 훅만 반대 방식으로 남아 있다.
- **개선안**: 건드린 파일이 `project.source_root`(기본 `src`) 또는 `tests/` 아래일 때만
  테스트·린트를 실행하는 허용 목록 방식으로 전환한다. 매니페스트를 못 읽는 경우
  (`ManifestUnavailable`)의 fail-closed 동작은 그대로 유지한다.
- **대상**: `.claude/hooks/post_write_check.py`
- **난이도**: 하

### 14. `/init` 5단계가 커밋 분리 규칙(0008)과 충돌한다

- **문제**: `/init` 5단계는 `models.*` 오버라이드를 `.claude/agents/<이름>.md` 프론트매터에
  덮어쓰라고 지시한다. 그런데 `.claude/agents/`는 `.githooks/pre-commit`의 "하네스 버킷"이고
  `project.yaml`은 "프로젝트 버킷"이라, `/init` 한 번의 결과물(두 파일 다 수정됨)을 커밋하려면
  pre-commit이 차단한다. `0008`이 agents 파일을 "프로젝트 내용이 절대 안 섞이는 순수
  인프라"로 분류했는데, `/init`의 model 오버라이드는 정확히 프로젝트별 값이다 — 분류 근거와
  실제 워크플로우가 모순.
- **개선안(택1)**: (a) `init.md` 5단계에 "agents 파일 변경은 하네스 버킷이므로 `project.yaml`과
  별도 커밋으로 나눠야 한다"를 명시 (가장 단순, 문서만). (b) `0008`의 분류를 재검토해
  `.claude/agents/`를 강제 목록에서 뺀다 (model 프론트매터가 프로젝트별 값이라는 근거로 —
  단, 이러면 에이전트 role 정의 개선의 cherry-pick 보호도 같이 사라지는 트레이드오프).
  어느 쪽이든 결정 로그를 남길 것. (a) 권장.
- **대상**: `.claude/commands/init.md` 또는 `.githooks/pre-commit` + `0008` 갱신
- **난이도**: 하 (판단 포함)

## P2 — 정합성·운영

### 15. task_id 정규식이 두 파일에 중복 정의돼 있고, 하이픈을 불허한다

- **문제**: `TASK_ID_RE`가 `update_board.py`와 `description_gate.py`에 각각 정의되어 있어
  한쪽만 바꾸면 조용히 어긋난다 (`0009` "남은 것"에 이미 경고됨). 그리고 패턴이
  `[A-Za-z0-9_]+`라 하이픈을 불허한다 — **실사고**: 오케스트레이터가 `"[t-verify] ..."`로
  호출했다가 자기 훅에 차단당했다. 문서 어디에도 "task_id에 하이픈 금지"라는 규칙은 없다.
- **개선안**: ① 하이픈 허용 여부를 결정한다 (허용 권장 — `[A-Za-z0-9_-]+`). ② 두 파일의
  정규식을 동시에 같은 값으로 바꾸고, 각 정의 옆에 "이 정규식은 <상대 파일>에도 있다 — 같이
  바꿀 것" 상호 참조 주석을 단다 (공유 모듈로 빼는 건 과함 — 두 곳뿐이다). ③ 커맨드 문서의
  형식 안내(`"[<task_id>] ..."`)에 허용 문자를 한 줄로 명시한다.
- **대상**: `.claude/hooks/update_board.py`, `.claude/hooks/description_gate.py`,
  `.claude/commands/extend.md`(서브에이전트 호출 규칙 문단)
- **난이도**: 하

### 16. `runs/.current`가 커밋 가능한 상태다 (머신 로컬 상태인데)

- **문제**: `runs/.current`는 "지금 이 머신에서 활성인 run"을 가리키는 세션 상태인데
  `.gitignore`에 없다. 실수로 커밋되면 clone/pull 받은 팀원이 남의(또는 이미 끝난) run
  포인터를 상속받고, 훅들(`update_board`/`approval_gate`)이 그 엉뚱한 run을 기준으로
  동작한다. (실제로 이전 프로젝트 브랜치에서 untracked 상태로 계속 떠다녔다.)
- **개선안**: `.gitignore`에 `runs/.current` 추가. 이미 추적 중인 브랜치가 있으면
  `git rm --cached runs/.current`도 안내. `runs/README.md`의 `.current` 설명에 "커밋하지
  않는다(머신 로컬 상태)" 한 줄 추가.
- **대상**: `.gitignore`, `runs/README.md`
- **난이도**: 하

### 17. `pre-commit`이 `project.yaml`의 YAML 문법은 검증하지 않는다

- **문제**: `settings.json`(JSON)은 검증하면서 `project.yaml`은 안 한다. `project.yaml`이
  깨진 채 커밋되면 모든 훅이 `load_manifest()`에서 런타임 에러로 죽는데, 커밋 시점엔 아무도
  못 잡는다.
- **개선안**: `.githooks/pre-commit`의 기존 검증 블록(`PYBIN` 사용)에, 스테이징된 파일 중
  `.claude/project.yaml`이 있으면 `"$PYBIN" -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" ...`
  검사를 추가. 단 PyYAML이 없을 수 있으므로 `import yaml` 실패 시엔 경고만 하고 통과시킨다
  (pre-commit은 게이트가 아니라 보조 검사이므로 fail-open이 맞다 — `post_write_check`의
  fail-closed와 다른 이유를 주석으로 명시).
- **대상**: `.githooks/pre-commit`
- **난이도**: 하

### 18. 원격(CI) 검증이 전혀 없다 — hooksPath 안 켠 팀원의 커밋은 아무 검사도 안 받는다

- **문제**: 모든 검증(pre-commit, Claude Code 훅)이 로컬 opt-in이다. `core.hooksPath`를
  설정 안 한 팀원이 push하면 문법 깨진 훅, 잘못된 settings.json이 그대로 main에 들어온다.
- **개선안**: 최소 GitHub Actions 워크플로우 하나 — push/PR 시 `.claude/hooks/*.py`
  py_compile, `settings.json` JSON 검증, `project.yaml` YAML 검증, `.githooks/pre-commit`·
  `_pyrun.sh` `bash -n`. **작업 전에 사람에게 CI 도입 의사를 먼저 확인할 것** (`create.md`의
  CI 골격이 선택 사항인 것과 같은 원칙 — 팀이 다른 CI를 쓸 수도 있다).
- **대상**: `.github/workflows/harness-check.yml` (신규)
- **난이도**: 하~중

## P3 — 엣지 케이스·잔재

### 19. pytest "no tests ran"(exit 5)을 게이트 실패로 취급한다

- **문제**: `post_write_check`는 exit code가 0이 아니면 전부 실패로 본다. pytest는 테스트가
  하나도 수집되지 않으면 exit 5를 반환하므로, 테스트가 아직 없는 레거시 프로젝트에서
  `/init`이 `commands.test`를 채우는 순간 모든 소스 Write가 실패한다. `/create`는 5단계
  (테스트 골격 먼저)로 이걸 피하지만 `/extend`·`/maintain`(레거시 대상)에는 보호장치가 없다.
  **실사고**: 이 세션에서 README 작성 중 정확히 이 케이스(exit 5)로 게이트가 실패했다.
- **개선안(정책 결정 필요)**: (a) pytest에 한정해 exit 5를 "경고 후 통과"로 처리 (테스트
  러너별 exit code 의미가 달라서 명령 문자열에 `pytest` 포함 여부로 판단하는 휴리스틱이 됨),
  또는 (b) `/init` 3단계에 "테스트가 실제로 하나도 없으면 `commands.test`를 비워두고, 첫
  테스트를 만든 뒤에 채워라"는 안내 추가 (코드 변경 없음, 문서만). (b)가 원칙(훅은 단순하게)에
  더 맞음 — 어느 쪽이든 결정 로그를 남길 것.
- **대상**: (a)면 `.claude/hooks/post_write_check.py`, (b)면 `.claude/commands/init.md`
- **난이도**: 하

### 20. `.missing.json`이 빈 `{}`로 영구히 남는다

- **문제**: `update_board.py`가 누락이 전부 해소된 뒤에도 `runs/<run>/agents/.missing.json`을
  빈 `{}`로 다시 쓴다. 기능엔 지장 없지만, run 폴더를 감사 기록으로 커밋할 때 의미 없는
  파일이 따라 들어간다.
- **개선안**: `save_missing()`에서 dict가 비어 있으면 파일을 쓰는 대신 삭제한다
  (`os.remove` + `FileNotFoundError` 무시).
- **대상**: `.claude/hooks/update_board.py`
- **난이도**: 하

---

## 처리 완료 (2026-07-04)

1차 백로그 11개 항목(P1 1~4, P2 5·6·7, P3 8~11) 전부 처리됨. 상세는
`.claude/decisions/0009`~`0013`과 커밋 히스토리 참고. 요약:

- **1~4, 7, 9**: 구현 완료 — PyYAML fail-closed, hooksPath 확인 안내, description 규칙 훅
  강제(`description_gate.py`), `test_fast` 필드, pre-commit 문법 검증, 에이전트 정의 task_id
  준수 지시.
- **5**: `runs/archive/` 수동 컨벤션만 문서화 (`0012`).
- **6**: run 생성 전 "기존 진행 중 run 확인" 단계 추가 (`0011`).
- **8**: 모델 배정 실측 완료, 문제없음 (`0010`).
- **10**: python3/python 감지 래퍼(`_pyrun.sh`) 구현 — **Windows 실기 검증은 아직 안 됨,
  Windows 팀원 최초 사용 시 확인 필요** (`0013`).
- **11**: 도구화하지 않기로 결정 (`0008`).
