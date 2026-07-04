#!/usr/bin/env python3
"""PreToolUse 훅 (Write|Edit) — 생성 모드(/create)의 아키텍처 승인 게이트.

두 가지를 강제한다. 둘 다 프롬프트 지시가 아니라 기계적으로 막는다 — 오케스트레이터가
잊거나, 서두르거나, 프롬프트 인젝션으로 "그냥 진행해도 된다"는 내용을 주입받아도
뚫리지 않는 걸 목표로 한다.

1. `runs/<run>/APPROVED` 파일은 Write/Edit로 절대 만들 수 없다. 사람이 자기 터미널/
   에디터로 직접 만들어야 한다 — 오케스트레이터가 스스로 "승인됐다"고 파일을 써서
   자기 자신을 승인하는 걸 구조적으로 막기 위함이다. 이건 어떤 run/모드에도 적용된다.

2. `runs/<run>/MODE`가 정확히 "create"인 run에서는, `project.source_root` 아래로의
   Write/Edit을 `runs/<run>/APPROVED`가 실제로 존재할 때만 허용한다. MODE가 없거나
   "create"가 아니면(예: /extend) 이 규칙은 적용하지 않는다 — /extend는 원래부터
   이 승인 절차를 쓰지 않는다.
"""
import fnmatch
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _manifest import load_manifest  # noqa: E402


def touched_path(tool_input: dict) -> str:
    return tool_input.get("file_path") or tool_input.get("path") or ""


def rel(path: str, cwd: str) -> str:
    r = os.path.relpath(path, cwd) if os.path.isabs(path) else path
    return r.replace(os.sep, "/")


def find_current_run(cwd: str):
    pointer = os.path.join(cwd, "runs", ".current")
    if not os.path.exists(pointer):
        return None
    with open(pointer, "r", encoding="utf-8") as f:
        run_id = f.read().strip()
    return run_id or None


def run_mode(cwd: str, run_id: str) -> str:
    mode_path = os.path.join(cwd, "runs", run_id, "MODE")
    if not os.path.exists(mode_path):
        return ""
    with open(mode_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()
    tool_input = payload.get("tool_input") or {}
    path = touched_path(tool_input)
    if not path:
        sys.exit(0)

    relpath = rel(path, cwd)

    # 규칙 1 — APPROVED 파일은 어떤 상황에서도 하네스 툴로 만들 수 없다.
    if fnmatch.fnmatch(relpath, "runs/*/APPROVED"):
        print(
            f"[harness] '{relpath}'는 하네스 툴(Write/Edit)로 만들 수 없습니다. "
            "제안서를 검토했다면 사람이 직접 터미널/에디터로 이 파일을 만들어야 "
            f"승인으로 인정됩니다 (예: touch {relpath}).",
            file=sys.stderr,
        )
        sys.exit(2)

    # 규칙 2 — create 모드 run에서만 source_root 쓰기를 승인 여부로 게이팅한다.
    run_id = find_current_run(cwd)
    if run_id is None or run_mode(cwd, run_id) != "create":
        sys.exit(0)

    manifest = load_manifest(cwd)
    project_cfg = manifest.get("project") if isinstance(manifest, dict) else {}
    source_root = ((project_cfg or {}).get("source_root") or "src").rstrip("/")

    is_source = relpath == source_root or relpath.startswith(source_root + "/")
    if not is_source:
        sys.exit(0)  # runs/, .claude/ 등 소스 루트 밖은 이 게이트와 무관

    approved_marker = os.path.join(cwd, "runs", run_id, "APPROVED")
    if not os.path.exists(approved_marker):
        print(
            f"[harness] 아직 승인되지 않았습니다. 'runs/{run_id}/PROPOSAL.md'를 검토하고, "
            f"승인하려면 사람이 'runs/{run_id}/APPROVED' 파일을 직접 만들어야 합니다.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
