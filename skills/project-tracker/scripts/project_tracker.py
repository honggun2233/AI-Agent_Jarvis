# -*- coding: utf-8 -*-
"""project-tracker: C:\\project 하위 각 폴더의 PROJECT.md를 SSOT로 진척률 관리.

진척률 = override_pct(수동) 있으면 그 값, 없으면 완료 마일스톤 / 전체 x100.
PROJECT.md 포맷: frontmatter + '## 마일스톤' 체크박스 + 그 이후(메모 등) 자유 영역.
'## 마일스톤' 이후 다음 '## ' 헤더부터 끝까지는 원문 그대로 보존한다.
"""
import os, sys, json, argparse, re
from datetime import date

PROJECTS_ROOT = r"C:\project"
MD_NAME = "PROJECT.md"
FM_ORDER = ["name", "type", "override_pct", "status", "updated"]


def parse_md(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fm, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
        body = m.group(2)
    lines = body.splitlines()
    milestones, tail = [], ""
    ms_start = next((i for i, ln in enumerate(lines)
                     if re.match(r"^##\s+마일스톤\s*$", ln)), None)
    if ms_start is not None:
        j = ms_start + 1
        while j < len(lines):
            if re.match(r"^##\s+", lines[j]):
                break
            cm = re.match(r"^\s*-\s*\[([ xX])\]\s*(.+?)\s*$", lines[j])
            if cm:
                milestones.append({"title": cm.group(2).strip(),
                                   "done": cm.group(1).lower() == "x"})
            j += 1
        tail = "\n".join(lines[j:])
    return fm, milestones, tail


def progress(fm, milestones):
    ov = (fm.get("override_pct") or "").strip()
    if ov:
        try:
            return max(0, min(100, int(round(float(ov))))), "manual"
        except ValueError:
            pass
    if not milestones:
        return 0, "auto"
    done = sum(1 for m in milestones if m["done"])
    return round(done * 100 / len(milestones)), "auto"


def write_md(path, fm, milestones, tail):
    fm["updated"] = date.today().isoformat()
    pct, mode = progress(fm, milestones)
    name = fm.get("name") or os.path.basename(os.path.dirname(path))
    keys = [k for k in FM_ORDER if k in fm] + [k for k in fm if k not in FM_ORDER]
    fmblock = "\n".join(f"{k}: {fm[k]}".rstrip() for k in keys)
    cbs = "\n".join(f"- [{'x' if m['done'] else ' '}] {m['title']}"
                    for m in milestones) or "- (없음)"
    if not tail.strip():
        tail = "## 메모\n-"
    out = (f"---\n{fmblock}\n---\n\n"
           f"# {name}  ·  진척률 {pct}% ({'수동' if mode == 'manual' else '자동'})\n\n"
           f"## 마일스톤\n{cbs}\n\n{tail.strip()}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)


def load_all():
    res = []
    if not os.path.isdir(PROJECTS_ROOT):
        return res
    for d in sorted(os.listdir(PROJECTS_ROOT)):
        if d.startswith(("_", ".")):          # 백업/은퇴/숨김 폴더 제외 (scan과 일치)
            continue
        md = os.path.join(PROJECTS_ROOT, d, MD_NAME)
        if os.path.isfile(md):
            fm, ms, tail = parse_md(md)
            res.append({"folder": d, "path": md, "fm": fm,
                        "milestones": ms, "tail": tail})
    return res


def find_one(query):
    allp = load_all()
    for pr in allp:                                  # exact: folder or name
        if pr["folder"] == query or pr["fm"].get("name") == query:
            return pr
    for pr in allp:                                  # partial
        if query in pr["folder"] or query in (pr["fm"].get("name") or ""):
            return pr
    return None


def bar(pct, width=12):
    filled = round(pct * width / 100)
    return "█" * filled + "░" * (width - filled)


def fmt_line(pr):
    pct, mode = progress(pr["fm"], pr["milestones"])
    name = pr["fm"].get("name") or pr["folder"]
    flag = ""
    if pr["fm"].get("status") == "pending":
        flag = "  🆕추출대기"
    elif mode == "manual":
        flag = "  (수동)"
    done = sum(1 for m in pr["milestones"] if m["done"])
    total = len(pr["milestones"])
    cnt = f" [{done}/{total}]" if total else ""
    return f"  {bar(pct)} {pct:3d}%  {name}{cnt}{flag}"


def cmd_list():
    projects = load_all()
    if not projects:
        print("등록된 프로젝트가 없습니다. (project_scan.py를 먼저 실행하세요)")
        return
    groups = [("🚀 개인", "personal"), ("💼 회사", "work"), ("· 기타/미분류", None)]
    known = {"personal", "work"}
    for title, key in groups:
        if key is None:
            sub = [p for p in projects if p["fm"].get("type") not in known]
        else:
            sub = [p for p in projects if p["fm"].get("type") == key]
        if not sub:
            continue
        print(f"\n{title}")
        for pr in sub:
            print(fmt_line(pr))
    print()


def cmd_json():
    out = []
    for pr in load_all():
        pct, mode = progress(pr["fm"], pr["milestones"])
        done = sum(1 for m in pr["milestones"] if m["done"])
        out.append({
            "folder": pr["folder"],
            "name": pr["fm"].get("name") or pr["folder"],
            "type": pr["fm"].get("type", ""),
            "status": pr["fm"].get("status", "active"),
            "pct": pct, "mode": mode,
            "done": done, "total": len(pr["milestones"]),
        })
    print(json.dumps(out, ensure_ascii=False))


def cmd_show(query):
    pr = find_one(query)
    if not pr:
        print(f"프로젝트를 찾을 수 없습니다: {query}")
        sys.exit(1)
    pct, mode = progress(pr["fm"], pr["milestones"])
    name = pr["fm"].get("name") or pr["folder"]
    print(f"\n{name}  ·  진척률 {pct}% ({'수동' if mode == 'manual' else '자동'})")
    print(f"  폴더: {pr['path']}")
    print(f"  상태: {pr['fm'].get('status', 'active')}")
    if not pr["milestones"]:
        print("  마일스톤: (없음)")
    else:
        print("  마일스톤:")
        for m in pr["milestones"]:
            print(f"    [{'x' if m['done'] else ' '}] {m['title']}")
        remaining = [m["title"] for m in pr["milestones"] if not m["done"]]
        if remaining:
            print(f"  남은 일: {', '.join(remaining)}")
    print()


def _save(pr):
    write_md(pr["path"], pr["fm"], pr["milestones"], pr["tail"])


def cmd_done(query, title, done=True):
    pr = find_one(query)
    if not pr:
        print(f"프로젝트를 찾을 수 없습니다: {query}"); sys.exit(1)
    hit = next((m for m in pr["milestones"]
                if m["title"] == title or title in m["title"]), None)
    if not hit:
        print(f"마일스톤을 찾을 수 없습니다: {title}"); sys.exit(1)
    hit["done"] = done
    _save(pr)
    print(f"{'완료' if done else '해제'}: {pr['fm'].get('name', query)} / {hit['title']}")
    cmd_show(query)


def cmd_set(query, value):
    pr = find_one(query)
    if not pr:
        print(f"프로젝트를 찾을 수 없습니다: {query}"); sys.exit(1)
    if value.lower() == "auto":
        pr["fm"]["override_pct"] = ""
        print(f"{pr['fm'].get('name', query)}: 자동 계산으로 전환")
    else:
        pct = max(0, min(100, int(round(float(value)))))
        pr["fm"]["override_pct"] = str(pct)
        print(f"{pr['fm'].get('name', query)}: 진척률 {pct}% (수동)")
    _save(pr)


def cmd_add(query, title):
    pr = find_one(query)
    if not pr:
        print(f"프로젝트를 찾을 수 없습니다: {query}"); sys.exit(1)
    pr["milestones"].append({"title": title, "done": False})
    _save(pr)
    print(f"마일스톤 추가: {pr['fm'].get('name', query)} / {title}")


def cmd_remove(query, title):
    pr = find_one(query)
    if not pr:
        print(f"프로젝트를 찾을 수 없습니다: {query}"); sys.exit(1)
    before = len(pr["milestones"])
    pr["milestones"] = [m for m in pr["milestones"]
                        if not (m["title"] == title or title in m["title"])]
    if len(pr["milestones"]) == before:
        print(f"마일스톤을 찾을 수 없습니다: {title}"); sys.exit(1)
    _save(pr)
    print(f"마일스톤 삭제: {pr['fm'].get('name', query)} / {title}")


def cmd_note(query, text):
    pr = find_one(query)
    if not pr:
        print(f"프로젝트를 찾을 수 없습니다: {query}"); sys.exit(1)
    # 메모 섹션을 교체(없으면 추가)
    tail = pr["tail"]
    if re.search(r"^##\s+메모\s*$", tail, re.MULTILINE):
        tail = re.sub(r"(##\s+메모\s*\n).*?(\n##\s+|\Z)",
                      rf"\1- {text}\2", tail, count=1, flags=re.DOTALL)
    else:
        tail = (tail.rstrip() + f"\n\n## 메모\n- {text}").strip()
    pr["tail"] = tail
    _save(pr)
    print(f"메모 갱신: {pr['fm'].get('name', query)}")


def cmd_apply(query, src):
    pr = find_one(query)
    if not pr:
        print(f"프로젝트를 찾을 수 없습니다: {query}"); sys.exit(1)
    raw = sys.stdin.read() if src == "-" else open(src, encoding="utf-8").read()
    data = json.loads(raw)
    # 허용 형식: ["a","b"] 또는 [{"title":..,"done":..}, ..] 또는
    #            {"type":"personal","name":"..","milestones":[...]}
    if isinstance(data, dict):
        for k in ("type", "name"):
            if data.get(k):
                pr["fm"][k] = data[k]
        items = data.get("milestones", [])
    else:
        items = data
    milestones = []
    for it in items:
        if isinstance(it, str):
            milestones.append({"title": it, "done": False})
        else:
            milestones.append({"title": it["title"], "done": bool(it.get("done"))})
    pr["milestones"] = milestones
    pr["fm"]["status"] = "active"
    _save(pr)
    print(f"마일스톤 {len(milestones)}개 등록: {pr['fm'].get('name', query)}")
    cmd_show(query)


def main():
    ap = argparse.ArgumentParser(description="project-tracker")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--show", metavar="PROJECT")
    ap.add_argument("--done", nargs=2, metavar=("PROJECT", "MILESTONE"))
    ap.add_argument("--undone", nargs=2, metavar=("PROJECT", "MILESTONE"))
    ap.add_argument("--set", nargs=2, metavar=("PROJECT", "PCT|auto"))
    ap.add_argument("--add", nargs=2, metavar=("PROJECT", "MILESTONE"))
    ap.add_argument("--remove", nargs=2, metavar=("PROJECT", "MILESTONE"))
    ap.add_argument("--note", nargs=2, metavar=("PROJECT", "TEXT"))
    ap.add_argument("--apply", nargs=2, metavar=("PROJECT", "JSON|-"))
    args = ap.parse_args()

    if args.json:
        cmd_json()
    elif args.show:
        cmd_show(args.show)
    elif args.done:
        cmd_done(args.done[0], args.done[1], True)
    elif args.undone:
        cmd_done(args.undone[0], args.undone[1], False)
    elif args.set:
        cmd_set(args.set[0], args.set[1])
    elif args.add:
        cmd_add(args.add[0], args.add[1])
    elif args.remove:
        cmd_remove(args.remove[0], args.remove[1])
    elif args.note:
        cmd_note(args.note[0], args.note[1])
    elif args.apply:
        cmd_apply(args.apply[0], args.apply[1])
    else:
        cmd_list()


if __name__ == "__main__":
    main()
