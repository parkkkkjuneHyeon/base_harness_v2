# 결정: 프로젝트 전용 conda 환경 사용
날짜: 2026-07-04
상태: 확정

## 배경

`/create` 첫 실전 실행에서, 테스트 러너 골격을 만든 서브에이전트가 `neo4j`/`fastapi`/`pytest`/
`ruff`를 격리 없이 ambient(base) 파이썬에 설치했다. 팀원이 여럿이고 이 머신에 이미 다른
프로젝트용 conda 환경(`cg`, `locuster`, `web_search_agent`, `yesolla-ai`)들이 있는 걸 보면, 이
프로젝트도 전용 환경을 쓰는 게 기존 관례와 맞다.

## 결정

`conda create -n book-graph-rag python=3.11`로 전용 환경을 만들고, 의존성은 전부 여기 설치한다.
`project.yaml`의 `commands.test`/`commands.lint`도 `conda run -n book-graph-rag <명령>` 형태로
바꿔서, 훅(`post_write_check.py`)이나 사람이 직접 실행해도 항상 이 환경을 쓰게 한다.

## 근거

`conda run -n <env> <cmd>`는 셸 activate 스크립트를 소싱할 필요 없이 특정 conda 환경에서 명령
하나를 실행하는 표준 방법이라, 훅처럼 비대화형으로 실행되는 스크립트에서도 그대로 쓸 수 있다.

## 남은 것

- base 환경에 이미 설치된 동일 패키지들은 정리하지 않고 그대로 뒀다 — 무해한 흔한 패키지들이고,
  지우는 게 base에 의존하는 다른 작업을 건드릴 위험이 더 크다고 판단했다. 필요하면 별도로 정리.
- 서브에이전트에게 위임하는 스펙에 "의존성 설치는 반드시 프로젝트 전용 환경에"라는 규칙을
  명시적으로 넣어야 한다 — 이번엔 사람이 사후에 발견해서 고쳤지만, 다음부터는 스펙 단계에서
  막는 게 낫다.
