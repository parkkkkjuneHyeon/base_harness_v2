---
description: 프로젝트 매니페스트(.claude/project.yaml)를 스캔·질문을 통해 만들거나 갱신합니다.
argument-hint: (선택) 다시 채울 항목 이름
---

`.claude/project.yaml`을 만들거나 갱신합니다. 이 파일은 이후 모든 세션이 참조하는 단일 진실
소스입니다 — 프로젝트 성숙도(신규/레거시) 같은 판단을 매번 다시 추측하지 않기 위한 것입니다.

## 절차

1. `.claude/project.yaml`이 이미 있으면 읽고, 무엇이 비어 있는지 확인합니다.
2. 저장소를 가볍게 스캔합니다 — 언어/프레임워크(스택), 기존 테스트 명령(package.json / Makefile /
   pyproject.toml / pytest.ini 등에서 추정), 이미 브랜치 보호 규칙이 있는지.
3. 스캔으로 못 채운 항목은 사람에게 직접 묻습니다. 특히:
   - `project.maturity` — 신규(new)인지 레거시(legacy)인지. **추측하지 말고 반드시 사람에게
     확인**합니다. 이후 모든 모드가 이 값을 그대로 참조합니다.
   - `commands.test`, `commands.lint` — 훅(`post_write_check.py`)이 그대로 실행할 명령이므로
     정확해야 합니다. 비워두면 해당 게이트는 조용히 건너뜁니다.
   - `models.*` — 서브에이전트 모델을 기본값과 다르게 쓰고 싶은지 묻습니다 (팀마다 비용 민감도가
     다를 수 있습니다). 비워두면 각 서브에이전트 파일의 기본값을 그대로 씁니다.
4. `.claude/project.yaml`을 채워서 저장합니다.
5. **`models.*`에 값이 채워진 항목이 있으면**, 해당하는 `.claude/agents/<이름>.md` 파일을 열어
   프론트매터의 `model:` 값을 매니페스트 값으로 덮어씁니다.
   (예: `models.code-generator: sonnet` → `.claude/agents/code-generator.md`의 `model: haiku`를
   `model: sonnet`으로 수정)
6. `CLAUDE.md`의 컨벤션 섹션에 이번에 파악한 컨벤션을 요약해 추가합니다.
7. 무엇을 채웠는지, 무엇을 사람 확인으로 남겼는지 요약해서 보고합니다.

`$ARGUMENTS`가 주어졌으면 해당 항목만 다시 확인합니다.
