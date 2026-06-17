---
name: work-status
description: C:\project 로컬 폴더의 파일 변경 시각을 스캔해 회사 업무·개인 프로젝트의 최근 활동 현황을 집계한다.
---

# work-status

로컬 프로젝트 폴더의 최근 변경 활동을 추적한다. GitHub가 아닌 로컬 폴더 기반.

## 사용

```powershell
$env:PYTHONIOENCODING="utf-8"
cd C:\Users\Samsung\Jarvis

# 회사 프로젝트 전체 (ETF 상품/운용/지수, AI 포털)
python skills\work-status\scripts\work_status.py --work

# 단일 폴더 (예: 온기로)
python skills\work-status\scripts\work_status.py --folder "C:\project\ongiro 프로젝트"

# 기간 변경 (기본 24시간)
python skills\work-status\scripts\work_status.py --work --hours 48
```

## 출력

폴더별로 `last_modified`(가장 최근 활동), `recent_count`(기간 내 변경 파일 수), `recent_files`(상위 5개)를 반환.

## 추적 대상 (회사)

`work_status.py` 상단 `WORK_PROJECTS` 딕셔너리에서 관리. 프로젝트 추가/삭제 시 여기 수정.

`.git`, `node_modules`, `__pycache__` 등 노이즈 폴더와 `.pyc/.log/.tmp` 등은 집계에서 제외.

## morning-briefing 연동

모닝 브리핑(`skills/morning-briefing`)의 🚀 개인 프로젝트 / 💼 회사 업무 섹션이 이 스킬을 호출한다.
