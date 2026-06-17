# -*- coding: utf-8 -*-
"""project_scan: C:\\project 하위 폴더를 훑어 PROJECT.md 없는 폴더에
pending 템플릿을 자동 생성한다. LLM 호출 없음(토큰 0).

--report : 이번에 새로 만든 폴더명만 한 줄씩 출력(후속 추출용).
"""
import os, sys, argparse
from datetime import date

PROJECTS_ROOT = r"C:\project"
MD_NAME = "PROJECT.md"
EXCLUDE_EXACT = {"repo_temp"}
EXCLUDE_PREFIX = ("_", ".")          # 백업/캐시/숨김 폴더
PERSONAL = {"urango1", "ongiro 프로젝트"}

TEMPLATE = """---
name: {name}
type: {type}
override_pct:
status: pending
updated: {date}
---

# {name}  ·  진척률 0% (자동)

## 마일스톤
- (없음)

## 메모
-
"""


def excluded(name):
    return name in EXCLUDE_EXACT or name.startswith(EXCLUDE_PREFIX)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()

    if not os.path.isdir(PROJECTS_ROOT):
        print(f"경로 없음: {PROJECTS_ROOT}", file=sys.stderr)
        sys.exit(1)

    created = []
    for d in sorted(os.listdir(PROJECTS_ROOT)):
        full = os.path.join(PROJECTS_ROOT, d)
        if not os.path.isdir(full) or excluded(d):
            continue
        md = os.path.join(full, MD_NAME)
        if os.path.isfile(md):
            continue
        ptype = "personal" if d in PERSONAL else "work"
        with open(md, "w", encoding="utf-8") as f:
            f.write(TEMPLATE.format(name=d, type=ptype,
                                    date=date.today().isoformat()))
        created.append(d)

    if args.report:
        for d in created:
            print(d)
    else:
        print(f"신규 {len(created)}개 PROJECT.md 생성" if created else "신규 없음")
        for d in created:
            print(f"  + {d}")


if __name__ == "__main__":
    main()
