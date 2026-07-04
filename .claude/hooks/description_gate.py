#!/usr/bin/env python3
"""PreToolUse 훅 (Agent) — code-generator/impact-analyzer/verifier 호출의 description 형식을 강제.

`update_board.py`의 보고 누락 자동 감지(`.claude/decisions/0006` 참고)는 Agent 호출의
`description`이 `"[<task_id>] <설명>"` 형식일 때만 작동한다. 지금까지는 이게 프롬프트
지시(`.claude/commands/*.md`)로만 존재해서, 오케스트레이터가 잊으면 감지가 조용히 꺼졌다
(원칙 2번 "규칙은 훅으로 강제한다"과 어긋남 — `.claude/decisions/0006` "남은 것" 참고).

실측 결과, PreToolUse 페이로드의 `tool_input`에 `subagent_type`/`description`이 이미
그대로 들어있는 걸 확인했다 (Agent 도구 호출 시점, 서브에이전트가 실행되기 전). 그래서
이 훅은 세 서브에이전트(code-generator/impact-analyzer/verifier) 호출만 골라서, description이
`"[<task_id>] ..."` 형식이 아니면 그 자리에서 막는다. 다른 subagent_type(general-purpose,
Explore 등)은 이 규칙 대상이 아니므로 건드리지 않는다.
"""
import json
import re
import sys

GATED_TYPES = {"code-generator", "impact-analyzer", "verifier"}
TASK_ID_RE = re.compile(r"^\[[A-Za-z0-9_]+\]")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    subagent_type = tool_input.get("subagent_type")
    if subagent_type not in GATED_TYPES:
        sys.exit(0)  # 이 규칙 대상이 아닌 subagent_type(general-purpose 등)은 통과

    description = tool_input.get("description") or ""
    if TASK_ID_RE.match(description):
        sys.exit(0)

    print(
        f"[harness] '{subagent_type}' 호출의 description이 \"[<task_id>] <짧은 설명>\" "
        f"형식이 아닙니다 (지금 값: {description!r}). 예: \"[t2] neo4j_uri 잔여 참조 검색\". "
        "이 형식이어야 update_board.py의 보고 누락 자동 감지가 동작합니다.",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
