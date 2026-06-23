"""C:\\project 하위 git repo들의 동기화 상태를 빠르게 점검(네트워크 fetch 없음).
표시 기준: 미커밋 변경 / 미push 커밋 / main·master가 아닌 브랜치 / .git 미연결.
문제 있는 repo만 출력. --all 주면 정상까지 전부."""
import os, sys, subprocess, argparse

PROJECT_ROOT = r"C:\project"
# .git 없어도 추적해야 할 중요 프로젝트(미연결 경고용)
WATCH_NONGIT = ["문서관리 솔루션 프로젝트"]


def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=8)
        return r.stdout.strip()
    except Exception:
        return ""


def repo_state(path):
    branch = git(path, "rev-parse", "--abbrev-ref", "HEAD") or "?"
    dirty = len([l for l in git(path, "status", "--porcelain").splitlines() if l.strip()])
    ahead = git(path, "rev-list", "--count", "@{u}..HEAD") or ""
    issues = []
    if branch not in ("main", "master"):
        issues.append(f"브랜치 {branch}")
    if ahead and ahead != "0":
        issues.append(f"미push {ahead}")
    if dirty:
        issues.append(f"미커밋 {dirty}")
    return branch, issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    lines = []
    if not os.path.isdir(PROJECT_ROOT):
        print("(C:\\project 없음)"); return
    for name in sorted(os.listdir(PROJECT_ROOT)):
        p = os.path.join(PROJECT_ROOT, name)
        if not os.path.isdir(p):
            continue
        low = name.lower()
        if "retired" in low or "backup" in low or name.startswith("_") or name == "repo_temp":
            continue
        if os.path.isdir(os.path.join(p, ".git")):
            branch, issues = repo_state(p)
            if issues:
                lines.append(f"⚠️ {name}: {' · '.join(issues)}")
            elif a.all:
                lines.append(f"✅ {name}: {branch} 동기화 OK")
        elif name in WATCH_NONGIT:
            lines.append(f"❌ {name}: .git 미연결(버전관리 밖)")
    if not lines:
        print("✅ 모든 repo 동기화 정상")
    else:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
