---
name: calendar-reader
description: Google Calendar에서 오늘과 이번 주 일정을 조회한다.
---

# Calendar Reader Skill

## 언제 사용하나
- 사용자가 일정, 약속, 캘린더, 오늘 뭐 있어? 라고 물을 때

## 사용법

오늘 일정:
```bash
python skills/calendar-reader/scripts/calendar_reader.py --today
```

이번 주 일정:
```bash
python skills/calendar-reader/scripts/calendar_reader.py --week
```
