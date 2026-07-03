#!/usr/bin/env python3
"""PreToolUse 훅 (Write|Edit) — 보호된 브랜치에서 쓰기 작업을 막는다.

결정 사항: 브랜치를 자동으로 만들거나 이름 짓지 않는다. 여기서는 "지금 보호된
브랜치에 있다"는 사실만 걸러서 차단하고, 실제 브랜치 생성/전환은 사람이 직접
한다. (.claude/decisions/0001-open-questions-round1.md 참고)
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _manifest import load_manifest  # noqa: E402


def current_branch(cwd: str):
    try:
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        if inside.returncode != 0:
            return None  # git 저장소가 아니면 검사하지 않는다
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd, capture_output=True, text=True, timeout=5,
        )
        return branch.stdout.strip() or None
    except Exception:
        return None  # git이 없거나 오류가 나면 막지 않는다 (안전한 쪽으로 실패)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # 입력을 못 읽으면 막지 않는다

    cwd = payload.get("cwd") or os.getcwd()

    branch = current_branch(cwd)
    if branch is None:
        sys.exit(0)

    manifest = load_manifest(cwd)
    branches_cfg = manifest.get("branches") if isinstance(manifest, dict) else None
    protected = (
        branches_cfg.get("protected")
        if isinstance(branches_cfg, dict) and branches_cfg.get("protected")
        else ["main", "master", "develop"]
    )

    if branch in protected:
        print(
            f"[harness] 지금 '{branch}' 브랜치입니다. 보호 대상 브랜치라 직접 쓰기 작업을 막습니다.\n"
            "기능 전용 브랜치를 만들고 전환한 뒤 다시 시도하세요. "
            "(브랜치 이름은 팀 컨벤션에 맞게 직접 정하세요 — 하네스가 자동으로 만들지 않습니다.)",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
