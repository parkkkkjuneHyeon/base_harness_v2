#!/usr/bin/env bash
# python3 또는 python 중 실제로 존재하는 것을 찾아 정확히 한 번만 실행한다.
#
# 왜 `python3 "$@" || python "$@"` 같은 흔한 패턴을 안 쓰는가: 우리 훅들은 정상적으로
# 막을 때 exit 2를 반환한다. 그 패턴을 쓰면 python3로 정상 실행되어 exit 2가 나온 것도
# "명령 실패"로 오인해서 python으로 다시 한번 실행해버린다 — post_write_check.py처럼
# 실제 테스트를 돌리는 훅에서는 이게 테스트를 두 번 돌리는 사고로 이어진다. 그래서
# `command -v`로 "존재 여부"만 먼저 확인하고, 찾은 인터프리터로 딱 한 번만 실행한다.
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$@"
elif command -v python >/dev/null 2>&1; then
  exec python "$@"
else
  echo "[harness] python3/python을 찾을 수 없습니다. Python 3이 설치되어 PATH에 있는지 확인하세요." >&2
  exit 1
fi
