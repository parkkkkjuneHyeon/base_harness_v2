#!/usr/bin/env python3
"""PreToolUse 훅 (Bash) — APPROVED 파일 생성 시도 차단.

approval_gate.py의 규칙 1과 동일한 목표: 오케스트레이터가 Claude Code의 Bash 도구를
써서 `runs/<run>/APPROVED` 파일을 만드는 걸 방지한다. 이건 휴리스틱이라 완벽하지 않다:
- "APPROVED"라는 문자열 없이 파일을 만드는 명령은 감지하지 못한다.
- 반대로 "APPROVED"를 언급만 하는 무해한 명령도 막는다 (예: APPROVED를 로그로 출력하는 명령).

오탐이 발생하면 해당 명령을 다른 표현으로 바꾸거나, 사람이 직접 자기 터미널에서 실행하면
된다. 사람이 자기 터미널에서 실행하는 승인 명령은 Claude Code 도구 경로 밖이므로
이 훅과 무관하다.
"""
import json
import sys


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""

    if "APPROVED" in command:
        print(
            "[harness] Bash 명령에 'APPROVED'가 포함되어 있어 차단합니다. runs/<run>/APPROVED는 사람이 자기 터미널에서 직접 만들어야 승인으로 인정됩니다 (approval_gate.py 규칙 1과 같은 이유). 승인 파일 존재 확인은 Bash 대신 Read/Glob 도구를 쓰세요.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
