---
name: github-monitor
description: 유랑고·온기로 GitHub 레포의 이슈, PR, 최근 커밋을 조회한다.
---

# GitHub Monitor Skill

## 언제 사용하나
- 유랑고, 온기로 개발 현황을 물어볼 때
- GitHub 이슈, PR 상태가 필요할 때

## 사용법

전체 레포 현황:
```bash
python skills/github-monitor/scripts/github_monitor.py --all
```

유랑고만:
```bash
python skills/github-monitor/scripts/github_monitor.py --repo urango
```

온기로만:
```bash
python skills/github-monitor/scripts/github_monitor.py --repo ongiro
```

## 참고
온기로 레포 경로는 scripts/github_monitor.py의 REPOS['ongiro'] 값을 직접 수정해 설정.
