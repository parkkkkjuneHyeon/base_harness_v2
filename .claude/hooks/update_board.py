#!/usr/bin/env python3
"""SubagentStop 훅 (code-generator|impact-analyzer|verifier) — 게시판 갱신.

code-generator / impact-analyzer / verifier가 끝날 때마다
runs/<현재 run>/agents/*.md 를 다시 스캔해서 summary.md를 다시 쓴다.

알려진 한계 (의도적으로 단순하게 둔 부분): 이 훅은 "보고를 빼먹었는지"를
판정하지 않는다. 같은 종류의 서브에이전트를 병렬로 여러 개 띄우면, 훅 입력
(agent_type만 주어지고 task_id는 없다)만으로는 지금 끝난 호출이 어떤
task_id에 해당하는지 구분할 수 없기 때문이다. 그래서 "전부 보고했는지"는
오케스트레이터가 dispatch한 task_id 개수와 summary.md 행 수를 직접 대조해서
확인한다 — .claude/commands/extend.md 5절 참고.
"""
import glob
import json
import os
import re
import sys

FIELD_RE = re.compile(r"^([a-z_]+):\s*(.*)$")


def find_current_run(cwd: str):
    pointer = os.path.join(cwd, "runs", ".current")
    if not os.path.exists(pointer):
        return None
    with open(pointer, "r", encoding="utf-8") as f:
        run_id = f.read().strip()
    if not run_id:
        return None
    run_dir = os.path.join(cwd, "runs", run_id)
    return run_dir if os.path.isdir(run_dir) else None


def parse_report(path: str) -> dict:
    fields = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            m = FIELD_RE.match(line.rstrip("\n"))
            if m:
                fields[m.group(1)] = m.group(2).strip()
    return fields


def build_summary(run_dir: str) -> str:
    agents_dir = os.path.join(run_dir, "agents")
    rows = []
    for path in sorted(glob.glob(os.path.join(agents_dir, "*.md"))):
        fields = parse_report(path)
        rows.append(
            (
                fields.get("task_id", "?"),
                fields.get("status", "?"),
                fields.get("summary", ""),
                os.path.basename(path),
            )
        )

    lines = [
        "# 진행 상황 요약 (자동 생성 — 직접 편집하지 마세요)",
        "",
        "| task_id | status | summary | report |",
        "|---|---|---|---|",
    ]
    for task_id, status, summary, fname in rows:
        lines.append(f"| {task_id} | {status} | {summary} | {fname} |")
    if not rows:
        lines.append("| (아직 보고 없음) |  |  |  |")
    return "\n".join(lines) + "\n"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()

    run_dir = find_current_run(cwd)
    if run_dir is None:
        sys.exit(0)  # 추적 중인 run이 없으면 관여하지 않는다

    os.makedirs(os.path.join(run_dir, "agents"), exist_ok=True)
    summary = build_summary(run_dir)
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)

    sys.exit(0)


if __name__ == "__main__":
    main()
