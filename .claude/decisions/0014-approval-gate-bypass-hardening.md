# 결정: /create 승인 게이트의 우회 경로 3개 차단
날짜: 2026-07-05
상태: 확정

## 배경

`approval_gate.py`(`0003` 참고)는 Write/Edit 매처에만 걸려 있어서, 목표("프롬프트 인젝션을
당해도 안 뚫린다")에 실질적인 구멍이 3개 있었다 (`IMPROVEMENTS.md` 12번):

1. **Bash로 APPROVED 생성** — `create.md` 4절이 사람용으로 안내하는 touch 명령을
   오케스트레이터가 Bash 도구로 직접 실행할 수 있었다.
2. **`runs/<run>/MODE` 변조** — Write/Edit로 내용을 `create`→`extend`로 바꾸면 게이트가 꺼짐.
3. **`runs/.current` 변조** — 포인터를 다른 run으로 바꿔도 꺼짐.

## 결정

- **2·3번 (확실한 차단)**: `approval_gate.py` 규칙 1을 확장해 `runs/*/MODE`와 `runs/.current`의
  Write/Edit도 차단한다. 정상적인 run 생성 경로(세 커맨드 문서의 1단계)는 이 파일들을 전부
  Bash(`printf ... >`)로 만들기 때문에, Write/Edit 차단으로 정상 흐름은 깨지지 않는다.
- **1번 (휴리스틱 차단)**: `bash_approved_gate.py`(PreToolUse, matcher: Bash)를 신설했다.
  Bash 명령 문자열에 `APPROVED`(대문자, 대소문자 구분)가 포함되면 차단한다.

## 근거 — 휴리스틱의 한계를 받아들인 이유

Bash로 파일을 만드는 방법은 무한히 많아(`touch`, `>`, python -c, base64 디코드...) 완벽한
차단은 불가능하다. 문자열 매칭 휴리스틱은:
- **거짓 음성**: "APPROVED"라는 리터럴 없이 파일을 만드는 명령(변수 조합 등)은 못 잡는다.
- **거짓 양성**: APPROVED를 언급만 하는 무해한 명령도 막는다. **실제로 이번 검증 중에
  경험했다** — 검증용 명령의 echo 주석에 'APPROVED'가 들어 있어서 훅이 그 명령 전체를
  차단했다. 오탐 시 명령을 다른 표현으로 바꾸면 되고, 훅 에러 메시지가 대안(존재 확인은
  Read/Glob)을 안내한다.

이 트레이드오프에도 넣는 이유: 게이트를 우회하는 "가장 뻔한 경로"(create.md에 그대로 적혀
있는 touch 명령을 복붙 실행)를 막는 것 자체가 가치이고, 정교한 우회는 이미 명백히 의도적인
행동이라 프롬프트 지시 위반이 명확해진다.

## 검증 (전부 실측)

- `runs/.current` Write 페이로드 → exit 2, `runs/*/MODE` Write → exit 2,
  `runs/*/summary.md` Write → exit 0 (오탐 없음).
- Bash 훅: `touch runs/x/<승인파일명>` → exit 2, 커맨드 치환 형태
  (`echo done > "runs/$(cat runs/.current)/<승인파일명>"`) → exit 2, `ls runs/` /
  `git commit -m ...` → exit 0.
- settings.json 등록 직후 실제 세션에서 훅이 즉시 활성화되어 위의 거짓 양성 사례를
  직접 발생시킴 — 등록·동작 모두 라이브로 확인됨.

## 남은 것

- 거짓 음성은 구조적으로 존재한다 — 이 훅은 "완벽한 벽"이 아니라 "가장 뻔한 문을 잠그는 것".
- macOS의 대소문자 무시 파일시스템에서는 소문자 `approved` 파일 생성으로도
  `os.path.exists("APPROVED")`가 참이 될 수 있다 — 소문자까지 매칭하면 오탐(예: 파일명
  `bash_approved_gate.py` 언급)이 급증해서 일부러 대문자만 매칭했다. 알려진 한계로 남긴다.
