import os, sys, json, argparse
from github import Github
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

TOKEN = os.getenv('GITHUB_PAT', '')
g = Github(TOKEN)

REPOS = {
    'urango': 'honggun2233/urango1',
    'ongiro': None
}


def get_repo_status(repo_name: str) -> dict:
    try:
        repo = g.get_repo(repo_name)
        open_issues = repo.get_issues(state='open')
        open_prs = repo.get_pulls(state='open')
        commits = repo.get_commits()

        issue_list = [{'number': i.number, 'title': i.title, 'created': str(i.created_at)[:10]}
                      for i in list(open_issues)[:5]]
        pr_list = [{'number': p.number, 'title': p.title, 'user': p.user.login}
                   for p in list(open_prs)[:5]]
        latest_commit = list(commits)[0] if commits.totalCount > 0 else None

        return {
            'repo': repo_name,
            'open_issues': repo.open_issues_count,
            'open_prs': len(pr_list),
            'latest_commit': {
                'message': latest_commit.commit.message[:80] if latest_commit else '',
                'author': latest_commit.commit.author.name if latest_commit else '',
                'date': str(latest_commit.commit.author.date)[:16] if latest_commit else ''
            },
            'issues': issue_list,
            'prs': pr_list
        }
    except Exception as e:
        return {'repo': repo_name, 'error': str(e)}


def get_all_status() -> list:
    result = []
    for name, repo_path in REPOS.items():
        if repo_path:
            result.append(get_repo_status(repo_path))
        else:
            result.append({'repo': name, 'status': '레포 경로 미설정'})
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action='store_true', help='전체 레포 현황')
    parser.add_argument('--repo', type=str, choices=['urango', 'ongiro'])
    args = parser.parse_args()

    if args.all:
        print(json.dumps(get_all_status(), ensure_ascii=False, indent=2))
    elif args.repo:
        repo_path = REPOS.get(args.repo)
        if repo_path:
            print(json.dumps(get_repo_status(repo_path), ensure_ascii=False, indent=2))
        else:
            print(json.dumps({'error': f'{args.repo} 레포 경로 미설정'}, ensure_ascii=False))
