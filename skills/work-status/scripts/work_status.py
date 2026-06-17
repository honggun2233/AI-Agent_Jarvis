import os, sys, json, argparse
from datetime import datetime, timedelta

# 회사 업무 추적 대상 폴더 (projects.md 진행 중 목록 기준)
WORK_PROJECTS = {
    'ETF 상품 개발': r'C:\project\ETF 상품 개발 프로젝트',
    'ETF 운용 시스템': r'C:\project\ETF 운용 시스템 개발 project',
    'ETF 지수 DATA': r'C:\project\ETF 지수 DATA 관리 project',
    'AI 포털 마이그레이션': r'C:\project\AI 포털 마이그레이션 프로젝트',
}

# 노이즈 폴더/확장자 제외 (의미 있는 변경만 집계)
IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
               '.next', 'dist', 'build', '.idea', '.vscode', '.cache', 'out',
               '.gradle', 'gradle', '.claude', '.expo', '.dart_tool',
               '.pytest_cache', '.mypy_cache', 'target', 'coverage', 'bin', 'obj'}
IGNORE_EXT = {'.pyc', '.pyo', '.log', '.tmp', '.lock',
              '.bin', '.class', '.jar', '.o', '.dll', '.exe'}


def scan_folder(path: str, hours: int = 24, max_files: int = 5) -> dict:
    if not os.path.isdir(path):
        return {'exists': False}
    cutoff = datetime.now() - timedelta(hours=hours)
    latest_mtime = None
    recent = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if os.path.splitext(f)[1].lower() in IGNORE_EXT:
                continue
            fp = os.path.join(root, f)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fp))
            except OSError:
                continue
            if latest_mtime is None or mtime > latest_mtime:
                latest_mtime = mtime
            if mtime > cutoff:
                recent.append((mtime, os.path.relpath(fp, path)))
    recent.sort(reverse=True)
    return {
        'exists': True,
        'last_modified': latest_mtime.strftime('%Y-%m-%d %H:%M') if latest_mtime else None,
        'recent_count': len(recent),
        'recent_files': [{'file': rel, 'modified': mt.strftime('%m-%d %H:%M')}
                         for mt, rel in recent[:max_files]],
    }


def scan_work(hours: int = 24) -> list:
    result = []
    for name, path in WORK_PROJECTS.items():
        info = scan_folder(path, hours=hours)
        info['name'] = name
        result.append(info)
    return result


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', action='store_true', help='회사 프로젝트 전체 변경 현황')
    parser.add_argument('--folder', type=str, help='단일 폴더 변경 현황')
    parser.add_argument('--hours', type=int, default=24)
    args = parser.parse_args()

    if args.work:
        print(json.dumps(scan_work(hours=args.hours), ensure_ascii=False, indent=2))
    elif args.folder:
        print(json.dumps(scan_folder(args.folder, hours=args.hours), ensure_ascii=False, indent=2))
    else:
        parser.print_help()
