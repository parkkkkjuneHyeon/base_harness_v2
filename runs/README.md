# runs/

오케스트레이터-서브에이전트 통신 게시판. `/extend`·`/create`·`/maintain`이 작업마다 폴더를 만든다.

## `<run>` 표기 규칙 (중요)

이 문서와 `create.md`·`extend.md`·`maintain.md`·`.claude/agents/*.md`에 나오는 `<run>`은 어떤 고정된 이름이
아니라 **1단계에서 실제로 만들어진 run 폴더의 정확한 이름**을 가리키는 자리표시자다. 예:
`20260703-161822_add-payment-retry_a1b2`.

- 이 값의 원본은 항상 `runs/.current`다. 오케스트레이터는 사람에게 보여줄 명령이나 서브에이전트
  에게 넘길 경로를 만들기 **직전에 `runs/.current`를 다시 읽어서** 그 값을 그대로 쓴다 — 대화
  앞부분에서 기억하고 있는 값을 손으로 다시 타이핑하지 않는다.
- **사람에게 보여줄 "읽기용" 경로**(예: 제안서를 열어볼 파일 위치)는 `<run>`을 실제 값으로
  치환한 구체적인 경로로 안내한다. 글자 그대로 `<run>`을 남기면, 사람이 복사해서 셸에
  붙여넣었을 때 `<`가 입력 리다이렉션으로 해석돼 전혀 다른 오류가 난다.
- **사람이 실행할 "명령"**(예: 승인)은 값을 문자열로 옮겨 적지 말고 `runs/.current`를 그
  자리에서 읽게 만든다: `touch "runs/$(cat runs/.current)/APPROVED"`. `date`를 승인 시점에
  다시 실행하는 건 안 된다 — run 폴더가 만들어진 시각과 다른 시각이 나와서 존재하지 않는
  경로를 가리키게 된다. 자세한 사용법은 `.claude/commands/create.md` 4절 참고.

```
runs/<YYYYMMDD-HHMMSS>_<슬러그>_<짧은해시>/
  MODE                # "extend" | "create" | "maintain" — approval_gate.py가 승인 게이트 적용 여부를 판단
  PROPOSAL.md          # /create 전용 — 아키텍처 제안서 (승인 게이트 대상)
  APPROVED             # /create 전용 — 사람이 직접 만들어야 하는 승인 마커.
                        # 하네스 툴(Write/Edit)로는 절대 못 만든다 (approval_gate.py가 항상 차단)
  summary.md          # 자동 생성 — task_id별 최신 status. 오케스트레이터가 매턴 읽는 파일.
  agents/
    <서브에이전트명>_<task_id>.md   # 상세 보고. 디버깅·감사용, 평소엔 안 읽음.

runs/.current          # 지금 활성 run 폴더 이름 (한 줄). update_board.py / approval_gate.py가 참조.
```

`summary.md`는 `.claude/hooks/update_board.py`가 서브에이전트가 끝날 때마다 자동으로 다시
쓴다 — 직접 편집하지 않는다. `agents/*.md`는 각 서브에이전트가 스스로 작성한다 (보고 스키마는
`.claude/agents/*.md` 참고). `APPROVED`는 사람이 자기 터미널/에디터로 직접 만든다 — 프로젝트
루트에서 `touch "runs/$(cat runs/.current)/APPROVED"` — 대화창에서 "승인했다"고 말하는 것만으로는
게이트가 풀리지 않는다.

**`task_id`는 한 run 안에서 유일해야 한다.** 보고 파일명이 `<서브에이전트명>_<task_id>.md`라서,
같은 `task_id`를 두 번 쓰면 먼저 쓴 보고가 덮어써져서 사라진다. `create.md`·`extend.md`·`maintain.md`가
예시로 `t1`을 보여주는데, 위임할 때마다 `t1`, `t2`, `t3`...처럼 새 값으로 올려가야 한다.

이 폴더는 그대로 사람이 보는 진행 상황 대시보드 역할도 한다 — 버전 관리에 포함해 감사 기록으로
남기는 것을 권장한다.

## 오래된 run 정리

완료된(`summary.md`가 전부 `done`인) run이 쌓여서 `runs/` 아래가 지저분해지면, 전용 커맨드나
자동 정리 도구 없이 사람이 직접 `runs/archive/`로 옮긴다 (예: `mkdir -p runs/archive && mv
runs/<완료된-run> runs/archive/`). `summary.md`는 감사 기록으로서 그대로 두고, 필요하면
`agents/` 아래 상세 보고만 지워서 용량을 줄인다. 전용 정리 커맨드는 이 수동 작업이 실제로
반복되어 고통스러워질 때 검토한다 (`.claude/decisions/0012` 참고).
