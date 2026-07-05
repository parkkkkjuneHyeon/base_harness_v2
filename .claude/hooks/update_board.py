#!/usr/bin/env python3
"""SubagentStop 훅 (code-generator|impact-analyzer|verifier) — 게시판 갱신 + 보고 누락 감지.

code-generator / impact-analyzer / verifier가 끝날 때마다
runs/<현재 run>/agents/*.md 를 다시 스캔해서 summary.md를 다시 쓴다.

보고 누락 감지: 오케스트레이터가 Agent 호출 시 description을 "[<task_id>] <설명>" 형식으로
지정하면, 이 훅은 SubagentStop 페이로드의 background_tasks[]에서 자기 agent_id에 해당하는
항목을 찾아 description에서 task_id를 파싱한다. 그 task_id에 해당하는 보고 파일
(agents/<agent_type>_<task_id>.md)이 없으면 runs/<run>/agents/.missing.json에 기록해두고
summary.md에 경고로 노출한다 — 나중에 보고가 들어오면 자동으로 사라진다.

description이 "[task_id]" 규칙을 따르지 않으면(과거 호출, 규칙 미준수 등) 이 감지는 조용히
건너뛴다 — 오탐보다 무동작이 낫다. 이 경우 "전부 보고했는지"는 여전히 오케스트레이터가
디스패치한 task_id 개수와 summary.md 행 수를 직접 대조해서 확인해야 한다.
"""
import glob
import json
import os
import re
import sys

FIELD_RE = re.compile(r"^([a-z_]+):\s*(.*)$")
# 이 정규식은 description_gate.py에도 정의되어 있다 — 바꿀 때 반드시 같이 바꿀 것.
TASK_ID_RE = re.compile(r"^\[([A-Za-z0-9_-]+)\]")


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


def build_summary(run_dir: str, missing: dict) -> str:
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

    if missing:
        lines.append("")
        lines.append("## ⚠ 보고 누락 감지")
        lines.append("")
        for key, info in sorted(missing.items()):
            lines.append(
                f"- `{key}` — 서브에이전트가 종료됐지만 `agents/{key}.md`가 없습니다. "
                f"(description: \"{info.get('description', '')}\")"
            )

    return "\n".join(lines) + "\n"


def load_missing(run_dir: str) -> dict:
    path = os.path.join(run_dir, "agents", ".missing.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_missing(run_dir: str, missing: dict) -> None:
    """누락이 전부 해소되면 빈 {} 파일을 남기지 않고 지운다 — run 폴더를 감사 기록으로 커밋할 때 잔재가 따라가지 않게."""
    path = os.path.join(run_dir, "agents", ".missing.json")
    if not missing:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(missing, f, ensure_ascii=False, indent=2)


def resolve_task_id(payload: dict):
    """이번에 끝난 호출의 (agent_type, task_id, description)을 payload에서 찾는다. 모르면 None."""
    agent_id = payload.get("agent_id")
    agent_type = payload.get("agent_type")
    if not agent_id or not agent_type:
        return None
    for task in payload.get("background_tasks", []):
        if task.get("id") == agent_id:
            description = task.get("description", "")
            m = TASK_ID_RE.match(description)
            if m:
                return agent_type, m.group(1), description
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()

    run_dir = find_current_run(cwd)
    if run_dir is None:
        sys.exit(0)  # 추적 중인 run이 없으면 관여하지 않는다

    agents_dir = os.path.join(run_dir, "agents")
    os.makedirs(agents_dir, exist_ok=True)

    missing = load_missing(run_dir)

    resolved = resolve_task_id(payload)
    if resolved is not None:
        agent_type, task_id, description = resolved
        key = f"{agent_type}_{task_id}"
        report_path = os.path.join(agents_dir, f"{key}.md")
        if os.path.exists(report_path):
            missing.pop(key, None)
        else:
            missing[key] = {"description": description}

    # 다른 호출에서 이미 감지된 누락도, 그 사이 보고가 들어왔으면 같이 해소한다.
    for key in list(missing.keys()):
        if os.path.exists(os.path.join(agents_dir, f"{key}.md")):
            missing.pop(key, None)

    save_missing(run_dir, missing)

    summary = build_summary(run_dir, missing)
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summary)

    sys.exit(0)


if __name__ == "__main__":
    main()
