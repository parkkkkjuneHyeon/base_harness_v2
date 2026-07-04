# 결정: description "[task_id]" 규칙을 PreToolUse 훅으로 강제
날짜: 2026-07-04
상태: 확정

## 배경

`update_board.py`의 보고 누락 자동 감지(`0006-subagentstop-missing-report-detection.md`)는
Agent 호출의 `description`이 `"[<task_id>] <설명>"` 형식일 때만 작동한다. 이 규칙은
`.claude/commands/*.md`에 프롬프트 지시로만 존재했고, 오케스트레이터가 잊으면 감지 기능
자체가 조용히 꺼졌다 — 원칙 2번("규칙은 훅으로 강제한다")과 어긋나는 상태였다
(`0006`의 "남은 것"에 이미 기록되어 있었음).

## 실측

바로 구현하지 않고, `PreToolUse` 훅이 `Agent` 도구 호출 시점에 실제로 어떤 정보를 받는지
먼저 덤프해서 확인했다 (0006 때와 같은 방식 — 가정으로 설계하지 않는다). 결과, 서브에이전트가
실행되기도 전인 `PreToolUse` 단계에서 이미 `tool_input.subagent_type`과
`tool_input.description`이 그대로 들어있었다:

```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Agent",
  "tool_input": {
    "description": "[t99] ...",
    "prompt": "...",
    "subagent_type": "verifier"
  }
}
```

즉 서브에이전트가 시작되기 전에 규칙 위반을 잡아서, 아예 실행을 막을 수 있다.

## 결정

`.claude/hooks/description_gate.py`(PreToolUse, matcher: `Agent`)를 추가했다.

- `tool_input.subagent_type`이 `code-generator`/`impact-analyzer`/`verifier` 중 하나일 때만
  검사한다. 그 외 타입(`general-purpose`, `Explore` 등)은 이 규칙 대상이 아니므로 건드리지
  않는다 — 이 셋 말고는 애초에 `update_board.py`의 `SubagentStop` 매처에도 안 걸리므로
  description 형식을 강제할 이유가 없다.
- `tool_input.description`이 `^\[[A-Za-z0-9_]+\]`로 시작하지 않으면 exit 2로 막고, 올바른
  형식과 예시를 안내한다.

## 근거

훅으로 옮기고 나니 결과가 이전보다 강해졌다 — 이전엔 "형식을 안 지키면 감지가 조용히
꺼진다"였는데, 이제는 "형식을 안 지키면 서브에이전트 호출 자체가 안 된다." 오케스트레이터가
규칙을 깜빡할 수 있는 여지 자체를 없앴다.

## 검증

실제로 세 가지 케이스를 직접 호출해서 확인했다:
1. `subagent_type: verifier` + 대괄호 없는 description → 차단됨 (`PreToolUse:Agent hook error`)
2. `subagent_type: verifier` + `"[t1] ..."` 형식 → 정상 디스패치됨
3. `subagent_type: general-purpose` + 대괄호 없는 description → 정상 디스패치됨 (규칙 대상 아님)

## 남은 것

- 정규식은 `[t1]`처럼 대괄호 안에 영숫자/밑줄만 허용한다. task_id 명명 규칙이 앞으로 달라지면
  (예: 하이픈 포함) 이 정규식도 같이 업데이트해야 한다.
- 이 훅은 `description`의 "형식"만 검사하지, 그 안의 `task_id`가 실제로 이번 run에서 유효한
  값인지(오타, 재사용 여부)는 검사하지 않는다 — 그건 여전히 `update_board.py`의 몫이다.
