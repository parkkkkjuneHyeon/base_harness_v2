# 결정: 서브에이전트 model 프론트매터 실제 적용 확인 (코드 변경 없음)
날짜: 2026-07-04
상태: 확정 — 검증 완료, 조치 불필요

## 배경

`.claude/agents/*.md`의 `model:` 프론트매터(code-generator/impact-analyzer는 `haiku`,
verifier는 `sonnet`)가 실제 디스패치에서 반영되는지 한 번도 확인된 적이 없었다
(`IMPROVEMENTS.md` 8번). 반영이 안 됐다면 원칙 3번("대량 생성은 code-generator(기본
Haiku)에게 맡긴다")의 비용 최적화 전제 자체가 무의미해진다.

## 검증

세 서브에이전트를 각각 더미 호출한 뒤, `~/.claude/projects/<프로젝트>/<session_id>/
subagents/agent-<agent_id>.jsonl` 트랜스크립트에서 실제 사용된 `model` 필드를 직접 grep했다
(SubagentStop/PreToolUse 훅 페이로드에는 `model` 필드가 없어서, 이 방법이 유일하게 확실한
확인 경로였다):

| 서브에이전트 | 선언(`model:`) | 실제 사용 모델 |
|---|---|---|
| `code-generator` | `haiku` | `claude-haiku-4-5-20251001` |
| `impact-analyzer` | `haiku` | `claude-haiku-4-5-20251001` |
| `verifier` | `sonnet` | `claude-sonnet-5` |

셋 다 프론트매터 선언과 실제 실행 모델이 정확히 일치했다.

## 결정

코드/문서 변경 없음 — 현재 동작이 의도대로 작동함을 확인만 했다. `IMPROVEMENTS.md`에서
8번 항목을 제거한다.
