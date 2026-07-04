#!/usr/bin/env python3
"""PostToolUse 훅 (Write|Edit) — 매니페스트에 정의된 테스트/린트를 실행한다.

이게 유지보수 모드의 회귀 게이트이자 기능추가 모드의 컨벤션 게이트다.
'설계 의도가 맞는지' 같은 해석이 필요한 판단은 여기서 하지 않는다 — 그건
verifier 서브에이전트(모델)의 몫이다. 여기서는 기계적으로 예/아니오로
판정 가능한 것만 다룬다 (decisions/0001 — Verifier 경계선 참고).

runs/ 와 .claude/ 밑, CLAUDE.md 변경은 건드리지 않는다 — 보고서/설정
파일까지 매번 테스트를 돌리면 낭비다.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _manifest import load_manifest, ManifestUnavailable  # noqa: E402

SKIP_PREFIXES = ("runs/", ".claude/", "CLAUDE.md")


def touched_path(tool_input: dict) -> str:
    return tool_input.get("file_path") or tool_input.get("path") or ""


def should_skip(path: str, cwd: str) -> bool:
    if not path:
        return True
    rel = os.path.relpath(path, cwd) if os.path.isabs(path) else path
    rel = rel.replace(os.sep, "/")
    return rel.startswith(SKIP_PREFIXES)


def run_cmd(cmd: str, cwd: str, label: str):
    if not cmd:
        return None
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=600,
        )
    except Exception as e:  # noqa: BLE001
        return f"{label} 실행 실패: {e}"
    if result.returncode != 0:
        tail = (result.stdout + result.stderr)[-2000:]
        return f"{label} 실패 (exit {result.returncode}):\n{tail}"
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()
    tool_input = payload.get("tool_input") or {}
    path = touched_path(tool_input)

    if should_skip(path, cwd):
        sys.exit(0)

    try:
        manifest = load_manifest(cwd)
    except ManifestUnavailable as e:
        print(f"[harness] {e}", file=sys.stderr)
        sys.exit(2)
    commands = manifest.get("commands") if isinstance(manifest, dict) else {}
    commands = commands or {}
    test_cmd = commands.get("test_fast") or commands.get("test")
    lint_cmd = commands.get("lint")

    if not test_cmd and not lint_cmd:
        sys.exit(0)  # 아직 /init에서 명령을 안 채웠으면 조용히 통과

    failures = []
    for cmd, label in ((test_cmd, "테스트"), (lint_cmd, "린트")):
        msg = run_cmd(cmd, cwd, label)
        if msg:
            failures.append(msg)

    if failures:
        print(
            "[harness] 게이트 실패 — 다음을 먼저 해결하세요:\n\n" + "\n\n".join(failures),
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
