# 결정: 이름 있는 서브에이전트를 못 부르는 실행 환경에서의 대체 방식
날짜: 2026-07-04
상태: 검증 완료 — 실제 Claude Code 환경에서는 문제 자체가 재현되지 않음 (아래 "검증 결과" 참고)

## 배경

`/create`를 실전 실행하는 과정에서, 이 실행 환경(orchestrator 세션)에는 `.claude/agents/*.md`에
정의한 이름 있는 서브에이전트(`code-generator`, `impact-analyzer`, `verifier`)를 이름으로 불러
호출하는 도구(Claude Code의 Task 같은 것)가 없다는 걸 발견했다. 이 환경에서 서브에이전트를
띄우는 유일한 방법은 고정된 타입 목록(`general-purpose` 등)만 받는 `Agent` 도구였다.

## 결정

당장은 `general-purpose` 타입으로 위임하되, 프롬프트 안에 `code-generator.md`의 규칙(스펙만
정확히 구현, 모호하면 blocked 대신 최선의 관례적 선택 후 보고, 정확한 경로에 보고 파일 작성)을
그대로 지시로 넣어서 최대한 근접하게 동작하게 했다. `SubagentStop` 훅(`update_board.py`)은
`agent_type`이 `code-generator|impact-analyzer|verifier`일 때만 발동하는데, `general-purpose`는
이 매처에 안 걸리므로 각 작업이 끝난 뒤 `update_board.py`를 오케스트레이터가 수동으로 한 번씩
실행해서 board를 갱신했다.

## 근거 / 한계

- 모델 비용 최적화(Haiku로 대량 생성) 원칙이 이 실행 환경에서는 실제로 강제되지 않는다 —
  `general-purpose`가 내부적으로 어떤 모델을 쓰는지 이 오케스트레이터는 제어할 수 없다. 실제
  Claude Code CLI(Task 도구가 있는 환경)에서 `/create`를 실행하면 이 문제는 없을 것으로 보인다.
- board 자동 갱신이 훅이 아니라 오케스트레이터의 수동 호출에 의존했다 — 원칙 2번("규칙은 훅으로
  강제한다")과 어긋난다. 이 세션에서만의 임시 우회다.
- 이건 하네스 설계의 결함이 아니라 **실행 환경의 도구 목록 차이**로 보인다. 실제 Claude Code
  세션에서 이 프로젝트를 열고 `/create`·`/extend`·`/maintain`을 실행하면 Task 도구를 통해
  이름 있는 서브에이전트가 정상적으로 호출될 것으로 예상한다 — 다음에 실제 Claude Code
  환경에서 한 번 검증이 필요하다.

## 실제로 만들어진 것 (이번 `/create` 실행 결과)

`src/{ingestion,extraction,graph_store,staging,retrieval,api,config}` 6개 모듈, `tests/` 대응
테스트 31개 전부 통과, `ruff` 클린. 상세는 `runs/20260704-000404_book-graph-rag_6c2f/summary.md`
및 `agents/code-generator_t1~t6.md` 참고.

## 검증 결과 (2026-07-04, 별도 세션)

실제 Claude Code 세션에서 `Agent` 도구의 `subagent_type`으로 `code-generator` /
`impact-analyzer` / `verifier`를 이름 그대로 지정해 호출할 수 있는지 확인했다.
`db-config-tls-swappable` run(`runs/20260704-112348_db-config-tls-swappable_0ba4`)에서
`impact-analyzer`를 `neo4j_uri` 잔여 참조 검색(t2)에 실제로 투입해 검증했다:

1. `subagent_type: "impact-analyzer"`로 호출이 성공했다 — `general-purpose` 우회가 필요 없었다.
2. 호출이 끝나자 오케스트레이터가 `update_board.py`를 수동으로 실행하지 않았는데도
   `SubagentStop` 훅이 자동 발동해 `summary.md`에 `t2` 행이 곧바로 추가됐다.

즉 이전 세션에서 관찰된 문제(이름 있는 서브에이전트 호출 불가, board 자동 갱신 실패)는 하네스
설계의 결함이 아니라 **그 세션의 실행 환경 자체가 Task 도구를 지원하지 않았기 때문**이었다는
가설이 맞았다. 실제 Claude Code 환경에서는 `general-purpose` 우회나 수동 `update_board.py`
호출이 필요 없다 — `/create`·`/extend`·`/maintain` 커맨드 문서에 있는 대로 이름 있는
서브에이전트를 그대로 호출하면 된다.

## 남은 것

- 모델 비용 최적화(haiku 배정)까지는 이번 검증에서 직접 확인하지 않았다 — `impact-analyzer.md`
  프론트매터의 `model: haiku`가 실제로 적용되는지는 다음 실행에서 비용/응답 특성으로 간접
  확인한다.
- 이 결정 자체는 "실행 환경 차이로 인한 임시 우회였다"는 기록으로 남기고, 신규 결정을 따로
  만들지 않는다 — 같은 사안의 결론이므로 이 파일에 이어서 적는다.
