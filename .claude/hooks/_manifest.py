"""project.yaml 매니페스트를 읽는 공용 헬퍼.

PyYAML에 의존한다 (pip install pyyaml). 잘못된 손수 파서로 조용히 잘못
읽는 것보다, 없으면 stderr에 분명히 알리고 빈 dict를 돌려주는 쪽을 택했다 —
호출하는 훅은 이 경우 해당 검사를 건너뛰고 exit 0으로 통과시킨다(안전한
쪽으로 실패).
"""
import os
import sys


class ManifestUnavailable(Exception):
    """PyYAML이 없어서 매니페스트를 못 읽을 때만 발생 — project.yaml이 아예 없는
    정상 상태와 구분하기 위함."""
    pass


def load_manifest(project_root: str) -> dict:
    path = os.path.join(project_root, ".claude", "project.yaml")
    if not os.path.exists(path):
        return {}

    try:
        import yaml  # type: ignore
    except ImportError:
        print(
            "[harness] .claude/project.yaml을 읽으려면 PyYAML이 필요합니다: "
            "pip install pyyaml",
            file=sys.stderr,
        )
        raise ManifestUnavailable(
            "PyYAML이 설치되지 않았습니다. pip install pyyaml을 실행하세요."
        )

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}
