# runs/

오케스트레이터-서브에이전트 통신 게시판. `/extend`가 작업마다 폴더를 만든다.

```
runs/<YYYYMMDD-HHMMSS>_<기능슬러그>_<짧은해시>/
  summary.md          # 자동 생성 — task_id별 최신 status. 오케스트레이터가 매턴 읽는 파일.
  agents/
    <서브에이전트명>_<task_id>.md   # 상세 보고. 디버깅·감사용, 평소엔 안 읽음.

runs/.current          # 지금 활성 run 폴더 이름 (한 줄). update_board.py 훅이 참조.
```

`summary.md`는 `.claude/hooks/update_board.py`가 서브에이전트가 끝날 때마다 자동으로 다시
쓴다 — 직접 편집하지 않는다. `agents/*.md`는 각 서브에이전트가 스스로 작성한다 (보고 스키마는
`.claude/agents/*.md` 참고).

이 폴더는 그대로 사람이 보는 진행 상황 대시보드 역할도 한다 — 버전 관리에 포함해 감사 기록으로
남기는 것을 권장한다.
