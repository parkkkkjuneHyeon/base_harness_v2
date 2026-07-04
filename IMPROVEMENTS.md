# 하네스 개선 백로그

이 문서는 하네스(harness_v1)의 알려진 한계와 개선 항목을 정리한 작업 목록이다. 각 항목은
배경 설명 없이도 바로 작업에 들어갈 수 있도록 문제 → 개선안 → 대상 파일 순으로 적었다.

**작업 시작 전에 반드시 읽을 것**: `CLAUDE.md`(모드·원칙), `README.md`(전체 구조),
`.claude/decisions/`(왜 이렇게 만들었는지). 특히 원칙 2번 — "기계적으로 판정 가능한 것만
훅으로 강제하고, 해석이 필요한 건 사람/verifier에게" — 를 어기는 개선안은 기각 대상이다.

**작업 방식**: `main`은 보호 브랜치다. `harness/<주제>` 브랜치를 만들어 작업하고, 하네스
인프라 파일과 그 외 파일을 한 커밋에 섞지 말 것 (`.githooks/pre-commit`이 막는다 —
`git config core.hooksPath .githooks` 최초 1회 설정 필요). 완료한 항목은 이 파일에서 지우고,
설계 판단이 필요했던 항목은 `.claude/decisions/`에 결정 로그를 남길 것.

---

## 전부 처리 완료 (2026-07-04 기준)

원래 있던 11개 항목(P1 1~4번, P2 5·6·7번, P3 8~11번) 전부 처리했다. 상세 내용과 근거는
`.claude/decisions/0009` ~ `0013`과 커밋 히스토리 참고. 요약:

- **1~4, 7, 9번**: 구현 완료 (PyYAML fail-closed, hooksPath 확인 안내, description 규칙
  훅 강제, `test_fast` 필드, pre-commit 문법 검증, 에이전트 정의 task_id 준수 지시).
- **5번(runs/ 아카이빙)**: 전용 도구 대신 `runs/README.md`에 수동 컨벤션만 문서화하기로
  결정 (`0012`) — 실제로 반복되어 아프면 그때 도구 검토.
- **6번(동시 세션 `.current` 충돌)**: 세션별 포인터 파일 대신, `/extend`·`/create`·
  `/maintain`의 run 생성 단계에 "기존 진행 중인 run이 있으면 먼저 물어보기" 가벼운 확인을
  추가 (`0011`).
- **8번(모델 배정 검증)**: 실측 완료, 문제없음 확인 (`0010`) — code-generator/
  impact-analyzer는 haiku, verifier는 sonnet으로 정확히 실행됨.
- **10번(Windows 호환)**: 팀에 실제 Windows 사용자가 있는 것으로 확인되어
  `command -v` 기반 python3/python 감지 래퍼(`.claude/hooks/_pyrun.sh`)를 구현.
  **단, macOS 환경에서 작업해 Windows 실기 검증은 못 했다 — Windows 팀원이 클론 후
  Write/Edit 훅과 `git commit`이 정상 작동하는지 반드시 확인할 것 (`0013`의 "남은 한계"
  참고).**
- **11번(CLAUDE.md/decisions/project.yaml 수동 이식)**: 새 도구 없이 현상 유지가 결정
  (`0008`에 이미 기록됨) — 이건 애초에 "할 일"이 아니라 "하지 않기로 한 결정"이었다.

## 다음에 새 항목이 생기면

이 섹션 형식(문제 → 개선안 → 대상 파일 → 난이도)을 그대로 쓰고, 위 "작업 방식"을 따를 것.
