# 결정: Windows 호환을 위해 python3/python 감지 래퍼 도입 (Windows 미검증)
날짜: 2026-07-04
상태: 확정 — 단, Windows 환경에서 아직 검증 못 함

## 배경

`.claude/settings.json`의 모든 훅이 `python3 ...`으로 등록되어 있는데, Windows는 보통
`python3`이 아니라 `python`(또는 `py -3`)만 PATH에 있다. 팀에 Windows(네이티브 git, WSL
아님)로 이 하네스를 쓸 팀원이 실제로 있다는 걸 확인한 뒤(`IMPROVEMENTS.md` 10번) 조치했다.

## 검토한 대안과 기각 이유

`python3 <스크립트> || python <스크립트>` 같은 흔한 셸 폴백 패턴을 처음 시도했지만 버그가
있어 기각했다: 우리 훅들은 정상적으로 막을 때 exit 2를 반환하는데, 이 패턴은 exit code로
폴백 여부를 판단하므로 **정상적인 차단도 "명령 실패"로 오인해서 `python`으로 또 실행한다.**
`post_write_check.py`처럼 실제 테스트/린트를 도는 훅에서는 이게 테스트를 두 번 돌리는
사고로 이어진다(`IMPROVEMENTS.md` 4번에서 막 줄인 비용을 도로 늘리는 셈이라 특히 나쁘다).

## 결정

`command -v`로 "존재 여부"만 먼저 확인하고, 찾은 인터프리터로 정확히 한 번만 실행하는
방식을 택했다.

- `.claude/hooks/_pyrun.sh` 신설: `command -v python3` → 있으면 `exec python3 "$@"`,
  없으면 `command -v python` → 있으면 `exec python "$@"`, 둘 다 없으면 에러 메시지 후 exit 1.
- `.claude/settings.json`의 모든 훅 등록을 `python3 .claude/hooks/X.py`에서
  `bash .claude/hooks/_pyrun.sh .claude/hooks/X.py`로 변경.
- `.githooks/pre-commit` 내부의 두 `python3` 호출(py_compile, JSON 검증)도 같은
  `command -v` 패턴으로 직접 수정 (별도 파일 없이 스크립트 상단에서 `PYBIN` 변수로 고정).

## 근거

`command -v`는 명령을 실행하지 않고 존재 여부만 확인하므로, 셸 폴백 패턴의 핵심 결함
(정상적인 비-zero exit과 "명령 없음"을 구분 못 하는 것)이 없다.

## 남은 한계 — 반드시 확인할 것

**이 수정은 Windows에서 실제로 테스트하지 못했다** (이 세션은 macOS 환경). 특히 다음이
불확실하다:

1. Claude Code가 Windows에서 `.claude/settings.json`의 `command` 문자열을 어떤 셸로
   실행하는지 모른다 — `bash`가 PATH에 있다는 전제 자체가 검증되지 않았다. Windows에
   Git Bash(Git for Windows 설치 시 기본 포함)가 PATH에 잡혀 있어야 `bash .claude/hooks/
   _pyrun.sh ...` 호출이 작동한다.
2. `.githooks/pre-commit`은 git이 자체 번들 셸로 실행하므로(Git for Windows 표준 동작)
   이 부분은 비교적 안전하다고 보지만, 이것도 실제 확인은 안 했다.

**Windows 팀원이 클론 후 반드시 확인해야 할 것**: 아무 파일이나 Write/Edit 해보고 훅이
정상 작동하는지(에러 없이 통과하거나, 의도한 대로 차단하는지), `git commit`이 정상적으로
`.githooks/pre-commit`을 타는지. 둘 중 하나라도 안 되면 `bash`가 PATH에 없는 것이므로,
Git for Windows 설치 시 "Git Bash Here"/PATH 옵션을 다시 확인하거나 WSL 사용을 검토한다.
