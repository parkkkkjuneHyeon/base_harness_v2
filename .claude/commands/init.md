---
description: 프로젝트 매니페스트(.claude/project.yaml)를 스캔·질문을 통해 만들거나 갱신합니다.
argument-hint: (선택) 다시 채울 항목 이름
---

`.claude/project.yaml`을 만들거나 갱신합니다. 이 파일은 이후 모든 세션이 참조하는 단일 진실
소스입니다 — 프로젝트 성숙도(신규/레거시) 같은 판단을 매번 다시 추측하지 않기 위한 것입니다.

## 절차

0. 지금 git 브랜치와 hooksPath 설정을 확인합니다.
   - **브랜치 확인**: `.claude/project.yaml`이 있으면 그 안의 `branches.protected`를,
     없으면(첫 실행이라 아직 매니페스트가 없는 경우) 기본값 `main`, `master`, `develop`을 기준으로
     삼습니다. 지금 브랜치가 여기 포함되면, 이 뒤 단계에서 하는 모든 저장(`project.yaml`,
     `CLAUDE.md`, `models.*` 오버라이드 시 `.claude/agents/*.md`)이 `branch_guard.py` 훅에
     막히므로, 시도하기 전에 사람에게 기능 전용 브랜치를 만들고 전환해달라고 요청하고 멈춥니다.
   - **hooksPath 확인**: `git config --get core.hooksPath`를 실행합니다. 결과가 `.githooks`가 아니면
     다음 명령을 실행하라고 안내합니다:
     ```
     git config core.hooksPath .githooks
     ```
     설정하지 않으면 `.githooks/pre-commit` 훅(커밋 분리)이 작동하지 않아, 하네스와 프로젝트 파일이
     섞인 커밋이 그대로 통과합니다. 안내 후 계속 진행합니다 (차단하지 않음).
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
