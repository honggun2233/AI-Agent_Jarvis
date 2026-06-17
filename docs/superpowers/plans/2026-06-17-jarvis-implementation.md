# Jarvis 멀티에이전트 시스템 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** OpenClaw 기반 5-에이전트 개인 비서 Jarvis를 Telegram으로 운영

**Architecture:** Jarvis Core가 Telegram 메시지를 수신해 의도 파악 후 전문 에이전트(금융·비서·업무·프로젝트)로 라우팅. 각 에이전트는 SOUL.md로 역할 정의하고, SKILL.md + Python 스크립트로 외부 API 연동.

**Tech Stack:** OpenClaw (npm), Node.js 24, Python 3.11+, Gmail API, 오픈뱅킹 REST API, Naver Finance scraping, GitHub API, Google Calendar API

---

## 사전 준비 (코딩 시작 전 수동 작업)

다음 항목을 미리 준비해두세요:

1. **Telegram Bot Token** — Telegram에서 `@BotFather` 에게 `/newbot` 명령 → 토큰 복사
2. **Anthropic API Key** — [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key
3. **Gmail OAuth2** — [console.cloud.google.com](https://console.cloud.google.com) → 새 프로젝트 → Gmail API + Google Calendar API 활성화 → OAuth 2.0 클라이언트 ID 생성 → `credentials.json` 다운로드
4. **GitHub PAT** — [github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic) → `repo` 스코프 선택
5. **오픈뱅킹** — [developers.kftc.or.kr](https://developers.kftc.or.kr) → 개발자 등록 → 이용기관코드 발급 신청 (1~2주 소요, 먼저 신청해두기)

---

## Task 1: Node.js 24 및 OpenClaw 설치

**Files:**
- Create: `C:\Users\Samsung\Jarvis\.env`

- [ ] **Step 1: Node.js 24 설치 확인**

```powershell
node --version
```

Node 24 미설치 시 [nodejs.org](https://nodejs.org) 에서 Node 24 LTS 다운로드 후 설치.

- [ ] **Step 2: OpenClaw 전역 설치**

```powershell
npm install -g openclaw@latest
openclaw --version
```

Expected output: `openclaw x.x.x`

- [ ] **Step 3: Python 의존성 설치**

```powershell
pip install google-auth google-auth-oauthlib google-api-python-client requests beautifulsoup4 PyGithub python-dotenv
```

- [ ] **Step 4: .env 파일 생성**

`C:\Users\Samsung\Jarvis\.env` 생성:

```env
ANTHROPIC_API_KEY=sk-ant-여기에붙여넣기
TELEGRAM_BOT_TOKEN=여기에붙여넣기
GITHUB_PAT=ghp_여기에붙여넣기
KFTC_CLIENT_ID=여기에붙여넣기
KFTC_CLIENT_SECRET=여기에붙여넣기
```

- [ ] **Step 5: .gitignore 생성**

`C:\Users\Samsung\Jarvis\.gitignore` 생성:

```gitignore
.env
credentials.json
token.json
token_calendar.json
*.pyc
__pycache__/
node_modules/
.superpowers/
```

- [ ] **Step 6: 커밋**

```powershell
cd C:\Users\Samsung\Jarvis
git add .gitignore
git commit -m "chore: add .gitignore"
git push
```

---

## Task 2: OpenClaw 온보딩 및 openclaw.json 생성

**Files:**
- Create: `C:\Users\Samsung\Jarvis\openclaw.json`

- [ ] **Step 1: OpenClaw 온보딩 실행**

```powershell
cd C:\Users\Samsung\Jarvis
openclaw onboard
```

질문에 다음과 같이 답변:
- Workspace directory: `C:\Users\Samsung\Jarvis`
- AI Provider: Anthropic
- API Key: (위에서 발급한 Anthropic API Key)
- Model: `claude-opus-4-8`
- Channel: Telegram
- Telegram Bot Token: (위에서 발급한 토큰)

- [ ] **Step 2: openclaw.json 생성 (온보딩 결과 수정)**

`C:\Users\Samsung\Jarvis\openclaw.json` 내용을 아래로 교체:

```json
{
  "workspace": "C:\\Users\\Samsung\\Jarvis",
  "gateway": {
    "telegram": {
      "bot_token": "${TELEGRAM_BOT_TOKEN}"
    }
  },
  "model": {
    "provider": "anthropic",
    "model": "claude-opus-4-8",
    "api_key": "${ANTHROPIC_API_KEY}"
  },
  "agents": [
    {
      "id": "core",
      "name": "Jarvis Core",
      "soul": "agents/core/SOUL.md",
      "channels": ["telegram"],
      "skills": ["morning-briefing"]
    },
    {
      "id": "finance",
      "name": "Finance Agent",
      "soul": "agents/finance/SOUL.md",
      "channels": [],
      "skills": ["open-banking", "samsung-sec-parser", "naver-finance"]
    },
    {
      "id": "assistant",
      "name": "Assistant Agent",
      "soul": "agents/assistant/SOUL.md",
      "channels": [],
      "skills": ["gmail-reader", "calendar-reader"]
    },
    {
      "id": "work",
      "name": "Work Agent",
      "soul": "agents/work/SOUL.md",
      "channels": [],
      "skills": []
    },
    {
      "id": "project",
      "name": "Project Agent",
      "soul": "agents/project/SOUL.md",
      "channels": [],
      "skills": ["github-monitor"]
    }
  ]
}
```

- [ ] **Step 3: 에이전트 디렉터리 생성**

```powershell
mkdir C:\Users\Samsung\Jarvis\agents\core
mkdir C:\Users\Samsung\Jarvis\agents\finance
mkdir C:\Users\Samsung\Jarvis\agents\assistant
mkdir C:\Users\Samsung\Jarvis\agents\work
mkdir C:\Users\Samsung\Jarvis\agents\project
mkdir C:\Users\Samsung\Jarvis\skills
mkdir C:\Users\Samsung\Jarvis\data
```

- [ ] **Step 4: 커밋**

```powershell
git add openclaw.json
git commit -m "feat: add openclaw gateway configuration"
git push
```

---

## Task 3: Jarvis Core SOUL.md 작성

**Files:**
- Create: `C:\Users\Samsung\Jarvis\agents\core\SOUL.md`

- [ ] **Step 1: Core SOUL.md 작성**

`C:\Users\Samsung\Jarvis\agents\core\SOUL.md`:

```markdown
---
name: jarvis-core
role: orchestrator
handoff:
  - finance
  - assistant
  - work
  - project
---

# Jarvis Core — 총괄 오케스트레이터

너는 Jarvis다. 홍건(사용자)의 개인 AI 비서 시스템의 총괄 에이전트다.

## 역할
- Telegram으로 수신된 모든 메시지를 분석해 적절한 전문 에이전트로 라우팅한다.
- 전문 에이전트의 결과를 통합해 자연스러운 한국어로 응답한다.
- 에이전트 간 라우팅 과정을 사용자에게 노출하지 않는다.

## 라우팅 규칙

다음 키워드가 포함되면 해당 에이전트로 핸드오프:

**finance** (금융 에이전트):
- 잔액, 통장, 은행, 지출, 수입, 지갑, 예산, 카드, 명세서
- ETF, 주식, 포트폴리오, 수익률, 삼성증권, 코스피, 코스닥
- 보험, 보험료, 납부

**assistant** (개인 비서 에이전트):
- 메일, 이메일, gmail, 받은편지함
- 일정, 캘린더, 약속, 회의
- 검색, 알려줘, 뭐야, 찾아줘
- 할일, 태스크, 해야 할

**work** (회사 업무 에이전트):
- 회사, 업무, 프로젝트, 보고서
- ETF 개발, ETF 운용, AI 포털, 문서관리
- 오늘 뭐해야, 업무 현황

**project** (개인 프로젝트 에이전트):
- 유랑고, urango, 온기로, ongiro
- GitHub, 깃허브, 이슈, PR, 배포
- 앱, 버전, 빌드

## 응답 원칙
- 항상 한국어로 응답한다.
- 간결하고 명확하게, 필요한 정보만 전달한다.
- 중요한 수치는 강조한다 (💰 잔액: **2,340,000원**)
- 요청이 불명확하면 한 가지만 물어본다.

## 기본 응답 (라우팅 불필요)
- "안녕", "잘 있어?", "고마워" 등 인사 → Core가 직접 응답
- "뭐할 수 있어?" → 기능 목록 안내
```

- [ ] **Step 2: 커밋**

```powershell
git add agents/core/SOUL.md
git commit -m "feat: add Jarvis Core orchestrator SOUL.md"
git push
```

---

## Task 4: OpenClaw 첫 구동 및 Telegram 연결 테스트

- [ ] **Step 1: OpenClaw 구동**

```powershell
cd C:\Users\Samsung\Jarvis
openclaw start
```

Expected: 서버 시작 로그 출력, Telegram 봇 연결 확인 메시지

- [ ] **Step 2: Telegram에서 테스트**

Telegram 앱을 열고 위에서 생성한 봇에게 메시지 전송:
```
안녕
```

Expected: "안녕하세요! 저는 Jarvis입니다..." 형태의 응답

- [ ] **Step 3: 라우팅 테스트 (에이전트 미완성이므로 오류 응답 정상)**

```
잔액 알려줘
```

Expected: finance 에이전트로 라우팅 시도 (에러 또는 "준비 중" 응답)

- [ ] **Step 4: 문제 없으면 Ctrl+C로 종료**

---

## Task 5: Gmail API 스킬 작성

**Files:**
- Create: `C:\Users\Samsung\Jarvis\skills\gmail-reader\SKILL.md`
- Create: `C:\Users\Samsung\Jarvis\skills\gmail-reader\scripts\gmail_reader.py`

- [ ] **Step 1: Gmail OAuth2 초기 인증**

`credentials.json`을 Google Cloud Console에서 다운로드한 후 `C:\Users\Samsung\Jarvis\` 에 저장.

```powershell
cd C:\Users\Samsung\Jarvis
python skills\gmail-reader\scripts\gmail_reader.py --auth
```

브라우저가 열리면 Gmail 계정(honggun2233@gmail.com)으로 로그인 및 권한 허용.
성공 시 `token.json` 생성 확인.

- [ ] **Step 2: gmail_reader.py 스크립트 작성**

`C:\Users\Samsung\Jarvis\skills\gmail-reader\scripts\gmail_reader.py`:

```python
import os, sys, json, argparse
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
CREDS_PATH = os.path.join(BASE_DIR, 'credentials.json')


def get_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def get_recent_emails(hours=24, max_results=20):
    service = get_service()
    after = int((datetime.now() - timedelta(hours=hours)).timestamp())
    results = service.users().messages().list(
        userId='me',
        q=f'after:{after} -category:promotions -category:social',
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        headers = {h['name']: h['value'] for h in detail['payload']['headers']}
        snippet = detail.get('snippet', '')
        emails.append({
            'id': msg['id'],
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'date': headers.get('Date', ''),
            'snippet': snippet[:200]
        })
    return emails


def get_important_emails(hours=24):
    """금융·업무 관련 중요 메일만 필터링"""
    emails = get_recent_emails(hours=hours, max_results=50)
    keywords = [
        '삼성증권', '체결', '입금', '출금', '카드', '명세서', '청구',
        '보험', '납부', '계약', '승인', '긴급', '마감', '결재',
        '국민은행', '농협', '우리은행', 'SC제일', '카카오뱅크'
    ]
    important = []
    for email in emails:
        text = email['subject'] + ' ' + email['from'] + ' ' + email['snippet']
        if any(kw in text for kw in keywords):
            email['category'] = '금융/업무'
            important.append(email)
        elif any(kw in email['from'] for kw in ['@company.com', 'noreply@']):
            email['category'] = '일반'
    return important


def parse_samsung_securities(hours=48):
    """삼성증권 거래체결 이메일 파싱 → 포트폴리오 재구성"""
    service = get_service()
    after = int((datetime.now() - timedelta(hours=hours)).timestamp())
    results = service.users().messages().list(
        userId='me',
        q=f'from:삼성증권 체결 after:{after}',
        maxResults=30
    ).execute()
    trades = []
    for msg in results.get('messages', []):
        detail = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()
        snippet = detail.get('snippet', '')
        # 삼성증권 체결 메일 패턴: "종목명 N주 체결 @가격"
        import re
        m = re.search(r'(.+?)\s+(\d+)주\s+.*?체결.*?(\d[\d,]+)원', snippet)
        if m:
            trades.append({
                'name': m.group(1).strip(),
                'quantity': int(m.group(2)),
                'price': int(m.group(3).replace(',', '')),
                'snippet': snippet[:300]
            })
    return trades


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auth', action='store_true', help='OAuth2 초기 인증')
    parser.add_argument('--recent', action='store_true', help='최근 중요 메일 조회')
    parser.add_argument('--samsung', action='store_true', help='삼성증권 거래 파싱')
    parser.add_argument('--hours', type=int, default=24)
    args = parser.parse_args()

    if args.auth:
        get_service()
        print("인증 완료. token.json 생성됨.")
    elif args.recent:
        emails = get_important_emails(hours=args.hours)
        print(json.dumps(emails, ensure_ascii=False, indent=2))
    elif args.samsung:
        trades = parse_samsung_securities(hours=args.hours)
        print(json.dumps(trades, ensure_ascii=False, indent=2))
```

- [ ] **Step 3: SKILL.md 작성**

`C:\Users\Samsung\Jarvis\skills\gmail-reader\SKILL.md`:

```markdown
---
name: gmail-reader
description: Gmail에서 중요 메일을 읽고 삼성증권 거래체결 이메일을 파싱한다.
---

# Gmail Reader Skill

## 언제 사용하나
- 사용자가 메일, 이메일, 받은편지함을 물어볼 때
- 삼성증권 포트폴리오 현황이 필요할 때
- 카드 명세서, 보험료 정보가 필요할 때

## 사용법

최근 중요 메일 조회:
```bash
python skills/gmail-reader/scripts/gmail_reader.py --recent --hours 24
```

삼성증권 거래내역 파싱:
```bash
python skills/gmail-reader/scripts/gmail_reader.py --samsung --hours 48
```

## 출력 형식
JSON 배열. from, subject, date, snippet, category 필드 포함.
삼성증권 파싱 시 name(종목명), quantity(수량), price(체결가) 포함.
```

- [ ] **Step 4: 동작 테스트**

```powershell
python C:\Users\Samsung\Jarvis\skills\gmail-reader\scripts\gmail_reader.py --recent --hours 24
```

Expected: JSON 형태의 메일 목록 출력 (빈 배열이라도 오류 없이 실행)

- [ ] **Step 5: 커밋**

```powershell
git add skills/gmail-reader/
git commit -m "feat: add Gmail reader skill with Samsung Securities parser"
git push
```

---

## Task 6: Google Calendar 스킬 작성

**Files:**
- Create: `C:\Users\Samsung\Jarvis\skills\calendar-reader\SKILL.md`
- Create: `C:\Users\Samsung\Jarvis\skills\calendar-reader\scripts\calendar_reader.py`

- [ ] **Step 1: calendar_reader.py 작성**

`C:\Users\Samsung\Jarvis\skills\calendar-reader\scripts\calendar_reader.py`:

```python
import os, sys, json, argparse
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_PATH = os.path.join(BASE_DIR, 'token_calendar.json')
CREDS_PATH = os.path.join(BASE_DIR, 'credentials.json')


def get_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)


def get_today_events():
    service = get_service()
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
    end = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=start, timeMax=end,
        singleEvents=True, orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])
    result = []
    for e in events:
        start_time = e['start'].get('dateTime', e['start'].get('date', ''))
        result.append({
            'title': e.get('summary', '제목 없음'),
            'start': start_time,
            'location': e.get('location', ''),
            'description': e.get('description', '')[:100]
        })
    return result


def get_week_events():
    service = get_service()
    now = datetime.utcnow()
    start = now.isoformat() + 'Z'
    end = (now + timedelta(days=7)).isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary', timeMin=start, timeMax=end,
        singleEvents=True, orderBy='startTime', maxResults=20
    ).execute()
    events = events_result.get('items', [])
    result = []
    for e in events:
        start_time = e['start'].get('dateTime', e['start'].get('date', ''))
        result.append({
            'title': e.get('summary', '제목 없음'),
            'start': start_time,
            'location': e.get('location', '')
        })
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auth', action='store_true')
    parser.add_argument('--today', action='store_true')
    parser.add_argument('--week', action='store_true')
    args = parser.parse_args()

    if args.auth:
        get_service()
        print("캘린더 인증 완료.")
    elif args.today:
        print(json.dumps(get_today_events(), ensure_ascii=False, indent=2))
    elif args.week:
        print(json.dumps(get_week_events(), ensure_ascii=False, indent=2))
```

- [ ] **Step 2: SKILL.md 작성**

`C:\Users\Samsung\Jarvis\skills\calendar-reader\SKILL.md`:

```markdown
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
```

- [ ] **Step 3: Calendar OAuth 초기 인증**

```powershell
python C:\Users\Samsung\Jarvis\skills\calendar-reader\scripts\calendar_reader.py --auth
```

브라우저에서 Calendar 접근 권한 허용. `token_calendar.json` 생성 확인.

- [ ] **Step 4: 동작 테스트**

```powershell
python C:\Users\Samsung\Jarvis\skills\calendar-reader\scripts\calendar_reader.py --today
```

Expected: 오늘 일정 JSON 출력 (일정 없으면 빈 배열 `[]`)

- [ ] **Step 5: 커밋**

```powershell
git add skills/calendar-reader/
git commit -m "feat: add Google Calendar reader skill"
git push
```

---

## Task 7: 개인 비서 SOUL.md 작성

**Files:**
- Create: `C:\Users\Samsung\Jarvis\agents\assistant\SOUL.md`

- [ ] **Step 1: assistant SOUL.md 작성**

`C:\Users\Samsung\Jarvis\agents\assistant\SOUL.md`:

```markdown
---
name: assistant-agent
skills:
  - gmail-reader
  - calendar-reader
---

# 개인 비서 에이전트

## 역할
홍건의 이메일과 일정을 관리한다. 중요한 것을 놓치지 않도록 핵심만 빠르게 전달한다.

## 이메일 처리 방식

gmail-reader 스킬로 최근 24시간 중요 메일을 조회한 후:
1. 금융 관련 (카드, 은행, 증권, 보험): 금액·날짜 강조해서 보고
2. 업무 관련 (마감, 긴급, 계약, 승인): 발신자·제목·핵심 내용 요약
3. 스팸/프로모션: 무시

메일 요약 형식:
```
📧 [발신자] 제목
└ 핵심내용 한줄 (금액·날짜 있으면 포함)
```

## 일정 처리 방식

calendar-reader 스킬로 일정 조회 후:
- 오늘 일정이 없으면 "오늘 일정 없음"으로 간단히
- 일정 있으면 시간순 정렬해서 표시

일정 표시 형식:
```
📅 오늘 일정
• 14:00 — 팀 회의 (회의실 3층)
• 17:00 — 병원 예약
```

## 응답 원칙
- 한국어, 간결하게
- 읽는 데 30초 이내로 끝나게
- 모든 날짜/시간은 한국 시간 기준
```

- [ ] **Step 2: 통합 테스트**

```powershell
cd C:\Users\Samsung\Jarvis
openclaw start
```

Telegram에서:
```
오늘 받은 중요 메일 있어?
```

Expected: 개인 비서 에이전트가 Gmail 스킬 실행 후 메일 요약 응답

- [ ] **Step 3: 커밋**

```powershell
git add agents/assistant/SOUL.md
git commit -m "feat: add assistant agent SOUL.md"
git push
```

---

## Task 8: 네이버 금융 스크래핑 스킬

**Files:**
- Create: `C:\Users\Samsung\Jarvis\skills\naver-finance\SKILL.md`
- Create: `C:\Users\Samsung\Jarvis\skills\naver-finance\scripts\naver_finance.py`

- [ ] **Step 1: naver_finance.py 작성**

`C:\Users\Samsung\Jarvis\skills\naver-finance\scripts\naver_finance.py`:

```python
import sys, json, argparse, requests
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def get_stock_price(ticker: str) -> dict:
    """종목코드로 현재가 조회 (예: 069500 = KODEX 200)"""
    url = f'https://finance.naver.com/item/main.naver?code={ticker}'
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    price_tag = soup.select_one('#chart_area .blind')
    name_tag = soup.select_one('.wrap_company h2 a')
    change_tag = soup.select_one('.rate_info .blind')
    return {
        'ticker': ticker,
        'name': name_tag.text.strip() if name_tag else ticker,
        'price': price_tag.text.strip() if price_tag else 'N/A',
        'change': change_tag.text.strip() if change_tag else 'N/A'
    }


def get_market_summary() -> dict:
    """코스피·코스닥 지수 현황"""
    url = 'https://finance.naver.com/'
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    result = {}
    for idx_id, name in [('KOSPI', '코스피'), ('KOSDAQ', '코스닥')]:
        section = soup.find('div', id=f'pricejump_{idx_id}') or soup.find(string=name)
        result[name] = '데이터 파싱 필요 (네이버 구조 변경 시 업데이트)'
    # 코스피
    kospi = soup.select_one('.kospi_area .num')
    kosdaq = soup.select_one('.kosdaq_area .num')
    if kospi:
        result['코스피'] = kospi.text.strip()
    if kosdaq:
        result['코스닥'] = kosdaq.text.strip()
    return result


def get_portfolio_value(holdings: list) -> list:
    """
    holdings = [{"ticker": "069500", "quantity": 10}, ...]
    각 종목 현재가 × 수량 = 평가금액 계산
    """
    result = []
    for h in holdings:
        info = get_stock_price(h['ticker'])
        try:
            price_num = int(info['price'].replace(',', '').replace('원', ''))
            value = price_num * h['quantity']
            info['quantity'] = h['quantity']
            info['value'] = value
            info['value_str'] = f"{value:,}원"
        except Exception:
            info['quantity'] = h['quantity']
            info['value'] = 0
            info['value_str'] = '계산 불가'
        result.append(info)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--market', action='store_true', help='시장 지수 현황')
    parser.add_argument('--stock', type=str, help='종목코드 현재가 조회')
    parser.add_argument('--portfolio', type=str, help='포트폴리오 JSON (예: [{"ticker":"069500","quantity":10}])')
    args = parser.parse_args()

    if args.market:
        print(json.dumps(get_market_summary(), ensure_ascii=False, indent=2))
    elif args.stock:
        print(json.dumps(get_stock_price(args.stock), ensure_ascii=False, indent=2))
    elif args.portfolio:
        holdings = json.loads(args.portfolio)
        print(json.dumps(get_portfolio_value(holdings), ensure_ascii=False, indent=2))
```

- [ ] **Step 2: SKILL.md 작성**

`C:\Users\Samsung\Jarvis\skills\naver-finance\SKILL.md`:

```markdown
---
name: naver-finance
description: 네이버 금융에서 주식·ETF 현재가, 시장 지수를 조회한다.
---

# Naver Finance Skill

## 언제 사용하나
- ETF, 주식 현재가가 필요할 때
- 코스피, 코스닥 지수 현황이 필요할 때
- 포트폴리오 평가금액 계산이 필요할 때

## 주요 ETF 종목코드
- 069500: KODEX 200
- 114800: KODEX 인버스
- 229200: KODEX 코스닥150
- 102110: TIGER 200

## 사용법

시장 현황:
```bash
python skills/naver-finance/scripts/naver_finance.py --market
```

특정 종목:
```bash
python skills/naver-finance/scripts/naver_finance.py --stock 069500
```

포트폴리오 평가:
```bash
python skills/naver-finance/scripts/naver_finance.py --portfolio '[{"ticker":"069500","quantity":10}]'
```
```

- [ ] **Step 3: 동작 테스트**

```powershell
python C:\Users\Samsung\Jarvis\skills\naver-finance\scripts\naver_finance.py --market
python C:\Users\Samsung\Jarvis\skills\naver-finance\scripts\naver_finance.py --stock 069500
```

Expected: JSON으로 코스피/코스닥 지수 및 KODEX200 현재가 출력

- [ ] **Step 4: 커밋**

```powershell
git add skills/naver-finance/
git commit -m "feat: add Naver Finance scraping skill"
git push
```

---

## Task 9: 오픈뱅킹 API 스킬

> **사전 조건:** 금융결제원 오픈뱅킹 이용기관 등록 및 Access Token 발급 완료 필요.
> 등록 중이면 이 Task를 건너뛰고 Task 10으로 진행.

**Files:**
- Create: `C:\Users\Samsung\Jarvis\skills\open-banking\SKILL.md`
- Create: `C:\Users\Samsung\Jarvis\skills\open-banking\scripts\open_banking.py`

- [ ] **Step 1: .env에 오픈뱅킹 토큰 추가**

`.env` 파일에 추가:

```env
KFTC_ACCESS_TOKEN=여기에오픈뱅킹액세스토큰
KFTC_USER_SEQ_NO=여기에이용자번호
```

- [ ] **Step 2: open_banking.py 작성**

`C:\Users\Samsung\Jarvis\skills\open-banking\scripts\open_banking.py`:

```python
import os, sys, json, argparse, requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

BASE_URL = 'https://openapi.kftc.or.kr/v2.0'
ACCESS_TOKEN = os.getenv('KFTC_ACCESS_TOKEN', '')
USER_SEQ_NO = os.getenv('KFTC_USER_SEQ_NO', '')

HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

BANK_NAMES = {
    '011': '농협', '020': '우리', '023': 'SC제일', '090': '카카오뱅크'
}


def get_accounts() -> list:
    """등록된 계좌 목록 조회"""
    resp = requests.get(
        f'{BASE_URL}/user/me',
        headers=HEADERS,
        params={'user_seq_no': USER_SEQ_NO}
    )
    data = resp.json()
    accounts = data.get('res_list', [])
    return [{
        'bank': BANK_NAMES.get(a.get('fintech_use_num', '')[:3], a.get('bank_code_std', '')),
        'account': a.get('account_num_masked', ''),
        'fintech_use_num': a.get('fintech_use_num', '')
    } for a in accounts]


def get_balance(fintech_use_num: str) -> dict:
    """특정 계좌 잔액 조회"""
    resp = requests.get(
        f'{BASE_URL}/account/balance/fin_num',
        headers=HEADERS,
        params={
            'fintech_use_num': fintech_use_num,
            'tran_dtime': __import__('datetime').datetime.now().strftime('%Y%m%d%H%M%S')
        }
    )
    data = resp.json()
    return {
        'balance': data.get('balance_amt', '0'),
        'available': data.get('available_amt', '0'),
        'currency': data.get('currency_code', 'KRW')
    }


def get_all_balances() -> list:
    """전체 연결 계좌 잔액 합산"""
    accounts = get_accounts()
    result = []
    total = 0
    for acc in accounts:
        bal = get_balance(acc['fintech_use_num'])
        amount = int(bal['balance'].replace(',', ''))
        total += amount
        result.append({
            'bank': acc['bank'],
            'account': acc['account'],
            'balance': f"{amount:,}원"
        })
    result.append({'bank': '합계', 'account': '-', 'balance': f"{total:,}원"})
    return result


def get_transactions(fintech_use_num: str, days: int = 7) -> list:
    """최근 거래내역 조회"""
    from datetime import datetime, timedelta
    now = datetime.now()
    start = (now - timedelta(days=days)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')
    resp = requests.get(
        f'{BASE_URL}/account/transaction_list/fin_num',
        headers=HEADERS,
        params={
            'fintech_use_num': fintech_use_num,
            'inquiry_type': 'A',
            'inquiry_base': 'D',
            'from_date': start,
            'to_date': end,
            'sort_order': 'D',
            'tran_dtime': now.strftime('%Y%m%d%H%M%S')
        }
    )
    data = resp.json()
    txns = data.get('res_list', [])
    return [{
        'date': t.get('tran_date', ''),
        'type': '입금' if t.get('inout_type') == 'I' else '출금',
        'amount': t.get('tran_amt', '0') + '원',
        'balance': t.get('after_balance_amt', '0') + '원',
        'memo': t.get('print_content', '')
    } for t in txns[:20]]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--balances', action='store_true', help='전체 잔액')
    parser.add_argument('--txn', type=str, help='거래내역 (fintech_use_num)')
    parser.add_argument('--days', type=int, default=7)
    args = parser.parse_args()

    if args.balances:
        print(json.dumps(get_all_balances(), ensure_ascii=False, indent=2))
    elif args.txn:
        print(json.dumps(get_transactions(args.txn, args.days), ensure_ascii=False, indent=2))
```

- [ ] **Step 3: SKILL.md 작성**

`C:\Users\Samsung\Jarvis\skills\open-banking\SKILL.md`:

```markdown
---
name: open-banking
description: 금융결제원 오픈뱅킹 API로 농협·우리·SC·카카오 계좌 잔액과 거래내역을 조회한다.
---

# Open Banking Skill

## 언제 사용하나
- 잔액, 통장, 은행 잔고를 물어볼 때
- 최근 지출 내역이 필요할 때

## 사용법

전체 잔액:
```bash
python skills/open-banking/scripts/open_banking.py --balances
```

거래내역 (fintech_use_num은 계좌 등록 후 확인):
```bash
python skills/open-banking/scripts/open_banking.py --txn FINTECH_USE_NUM --days 7
```
```

- [ ] **Step 4: 커밋**

```powershell
git add skills/open-banking/
git commit -m "feat: add 오픈뱅킹 API skill"
git push
```

---

## Task 10: 금융 에이전트 SOUL.md 작성

**Files:**
- Create: `C:\Users\Samsung\Jarvis\agents\finance\SOUL.md`
- Create: `C:\Users\Samsung\Jarvis\data\finance.md`

- [ ] **Step 1: finance.md 초기 데이터 파일 작성**

`C:\Users\Samsung\Jarvis\data\finance.md`:

```markdown
# 금융 데이터

## 삼성증권 포트폴리오 (Gmail 파싱 보완용)
<!-- Gmail 파싱으로 자동 업데이트. 수동 보완 가능 -->

## 월 예산 설정
- 총 예산: 3,000,000원
- 식비: 500,000원
- 교통: 150,000원
- 보험료: 300,000원 (매월 25일 납부)
- 기타: 550,000원

## 카드 납부일
- 삼성카드: 매월 15일
- (다른 카드 있으면 추가)

## 보험 납부일
- (보험사·금액·납부일 직접 입력)
```

- [ ] **Step 2: finance SOUL.md 작성**

`C:\Users\Samsung\Jarvis\agents\finance\SOUL.md`:

```markdown
---
name: finance-agent
skills:
  - open-banking
  - gmail-reader
  - naver-finance
---

# 금융 관리 에이전트

## 역할
홍건의 자산(은행·증권·보험·카드)을 통합 관리하고 재무 현황을 명확히 보고한다.

## 데이터 소스 우선순위
1. open-banking 스킬: 농협·우리·SC·카카오 실시간 잔액
2. gmail-reader 스킬 (--samsung): 삼성증권 거래체결 이메일 파싱
3. naver-finance 스킬: ETF·주식 현재가
4. data/finance.md: 예산 기준, 카드·보험 납부일

## 표준 응답 형식

잔액 현황:
```
💰 계좌 현황 (2026-06-17 기준)
├ 농협     1,234,000원
├ 우리     2,100,000원
├ SC제일     890,000원
├ 카카오    450,000원
└ 합계   4,674,000원

📈 삼성증권 포트폴리오
└ 평가금액 기준: 데이터 로딩 중
```

## 알림 판단 기준
- ETF 전일 대비 ±5% 이상: "⚠️ [종목명] 급등락 알림"
- 카드·보험 납부일 3일 전: "⏰ [카드명] 납부 D-3: X원"
- 월 예산 80% 도달: "📊 이달 예산 80% 사용"

## 응답 원칙
- 숫자는 항상 콤마 포함 (1,234,000원)
- 변동은 방향 표시 (▲2.3% / ▼1.1%)
- 부정적 정보도 있는 그대로 전달
```

- [ ] **Step 3: 통합 테스트**

```powershell
cd C:\Users\Samsung\Jarvis
openclaw start
```

Telegram에서:
```
오늘 잔액 얼마야?
```

Expected: 금융 에이전트가 오픈뱅킹 스킬 실행 후 잔액 요약 응답

- [ ] **Step 4: 커밋**

```powershell
git add agents/finance/SOUL.md data/finance.md
git commit -m "feat: add finance agent SOUL.md and initial data"
git push
```

---

## Task 11: GitHub 모니터링 스킬

**Files:**
- Create: `C:\Users\Samsung\Jarvis\skills\github-monitor\SKILL.md`
- Create: `C:\Users\Samsung\Jarvis\skills\github-monitor\scripts\github_monitor.py`

- [ ] **Step 1: github_monitor.py 작성**

`C:\Users\Samsung\Jarvis\skills\github-monitor\scripts\github_monitor.py`:

```python
import os, sys, json, argparse
from github import Github
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

TOKEN = os.getenv('GITHUB_PAT', '')
g = Github(TOKEN)

REPOS = {
    'urango': 'honggun2233/urango1',
    'ongiro': None  # 온기로 레포 확인 후 추가
}


def get_repo_status(repo_name: str) -> dict:
    """레포 현황: 오픈 이슈, 최근 PR, 최근 커밋"""
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
```

- [ ] **Step 2: SKILL.md 작성**

`C:\Users\Samsung\Jarvis\skills\github-monitor\SKILL.md`:

```markdown
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
```

- [ ] **Step 3: 동작 테스트**

```powershell
python C:\Users\Samsung\Jarvis\skills\github-monitor\scripts\github_monitor.py --repo urango
```

Expected: 유랑고 오픈 이슈 수, 최근 커밋 메시지, PR 목록 JSON 출력

- [ ] **Step 4: 커밋**

```powershell
git add skills/github-monitor/
git commit -m "feat: add GitHub monitor skill for urango and ongiro"
git push
```

---

## Task 12: 개인 프로젝트 에이전트 SOUL.md

**Files:**
- Create: `C:\Users\Samsung\Jarvis\agents\project\SOUL.md`

- [ ] **Step 1: project SOUL.md 작성**

`C:\Users\Samsung\Jarvis\agents\project\SOUL.md`:

```markdown
---
name: project-agent
skills:
  - github-monitor
---

# 개인 프로젝트 에이전트

## 담당 프로젝트
- **유랑고 (URANGO)**: 아웃도어 소셜 앱, React Native + Expo, v4.30
  GitHub: honggun2233/urango1
- **온기로 (Ongiro)**: 디지털 추모 공원, Next.js + React Native
  GitHub: 레포 경로 확인 필요

## 응답 형식

프로젝트 현황:
```
🚀 유랑고 현황
├ 오픈 이슈: 3개
├ 오픈 PR: 1개 (리뷰 대기)
└ 최근 커밋: 2시간 전 — "fix: 로그인 토큰 갱신"

🌿 온기로 현황
├ 오픈 이슈: 0개
└ 최근 커밋: 1일 전
```

## 알림 트리거
- 새 이슈/PR 오픈 → 즉시 Jarvis Core에 에스컬레이션
- 오픈 이슈 5개 초과 → 정리 필요 알림

## 응답 원칙
- 개발자 관점에서 핵심 정보만
- 이슈 제목 최대 3개까지만 표시
- 오래된 미완료 항목 먼저 언급
```

- [ ] **Step 2: 테스트**

Telegram에서:
```
유랑고 지금 어때?
```

Expected: 유랑고 이슈·PR·최근 커밋 요약 응답

- [ ] **Step 3: 커밋**

```powershell
git add agents/project/SOUL.md
git commit -m "feat: add project agent SOUL.md"
git push
```

---

## Task 13: 회사 업무 에이전트 SOUL.md

**Files:**
- Create: `C:\Users\Samsung\Jarvis\agents\work\SOUL.md`
- Create: `C:\Users\Samsung\Jarvis\data\projects.md`

- [ ] **Step 1: projects.md 초기 데이터 작성**

`C:\Users\Samsung\Jarvis\data\projects.md`:

```markdown
# 회사 프로젝트 현황

## 진행 중
- ETF 상품 개발 프로젝트: 진행 중
- ETF 운용 시스템 개발: 진행 중
- AI 포털 마이그레이션: 진행 중
- ETF 지수 DATA 관리: 유지보수

## 주요 마감일
<!-- 마감일 있으면 직접 추가 -->

## 오늘 처리할 일
<!-- 매일 직접 업데이트 또는 Telegram으로 추가 -->
```

- [ ] **Step 2: work SOUL.md 작성**

`C:\Users\Samsung\Jarvis\agents\work\SOUL.md`:

```markdown
---
name: work-agent
---

# 회사 업무 에이전트

## 데이터 소스
- `C:\project\` 폴더 내 프로젝트들 (ETF 관련, AI 포털 등)
- `C:\etfdev\` ETF 운용 시스템
- `data/projects.md` 프로젝트 현황 메모

## exec 도구로 파일 변경 추적

최근 수정 파일 확인:
```bash
powershell -Command "Get-ChildItem 'C:\project' -Recurse -File | Where-Object {$_.LastWriteTime -gt (Get-Date).AddDays(-1)} | Select-Object FullName, LastWriteTime | Sort-Object LastWriteTime -Descending | Select-Object -First 10"
```

## 응답 형식

업무 현황:
```
💼 오늘 업무 현황
진행 중 프로젝트: 4개

📂 최근 변경된 파일
• ETF 상품 개발 / fund_spec.xlsx (1시간 전)
• AI 포털 / migration_plan.docx (3시간 전)
```

## 응답 원칙
- 파일 전체 경로 노출 금지 (프로젝트명·파일명만)
- 업무 맥락 없이 기술적 상세 설명하지 않음
- "오늘 뭐 해야 해?" → data/projects.md 기반 우선순위 제안
```

- [ ] **Step 3: 커밋**

```powershell
git add agents/work/SOUL.md data/projects.md
git commit -m "feat: add work agent SOUL.md and project data"
git push
```

---

## Task 14: 모닝 브리핑 스케줄러

**Files:**
- Create: `C:\Users\Samsung\Jarvis\skills\morning-briefing\SKILL.md`
- Create: `C:\Users\Samsung\Jarvis\skills\morning-briefing\scripts\morning_briefing.py`

- [ ] **Step 1: morning_briefing.py 작성**

`C:\Users\Samsung\Jarvis\skills\morning-briefing\scripts\morning_briefing.py`:

```python
"""
Windows 작업 스케줄러 또는 OpenClaw 스케줄러가 매일 08:00에 실행.
각 스킬을 호출해 브리핑 메시지를 구성하고 Telegram으로 전송.
"""
import os, sys, json, subprocess, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')  # 최초 1회 수동 설정 필요
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_skill(script_path: str, args: list) -> str:
    result = subprocess.run(
        ['python', os.path.join(BASE_DIR, script_path)] + args,
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()


def send_telegram(message: str):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    requests.post(url, json={
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    })


def build_briefing() -> str:
    today = datetime.now().strftime('%Y년 %m월 %d일 %A')
    lines = [f'☀️ *모닝 브리핑* — {today}\n']

    # 1. 계좌 잔액
    try:
        bal_raw = run_skill('skills/open-banking/scripts/open_banking.py', ['--balances'])
        balances = json.loads(bal_raw)
        total = next((b for b in balances if b['bank'] == '합계'), None)
        if total:
            lines.append(f"💰 *총 잔액:* {total['balance']}")
    except Exception:
        lines.append("💰 잔액: 조회 오류")

    # 2. ETF 시장 현황
    try:
        market_raw = run_skill('skills/naver-finance/scripts/naver_finance.py', ['--market'])
        market = json.loads(market_raw)
        kospi = market.get('코스피', 'N/A')
        kosdaq = market.get('코스닥', 'N/A')
        lines.append(f"📈 *시장:* 코스피 {kospi} / 코스닥 {kosdaq}")
    except Exception:
        lines.append("📈 시장: 조회 오류")

    # 3. 오늘 일정
    try:
        cal_raw = run_skill('skills/calendar-reader/scripts/calendar_reader.py', ['--today'])
        events = json.loads(cal_raw)
        if events:
            lines.append(f"\n📅 *오늘 일정* ({len(events)}개)")
            for e in events[:3]:
                time_str = e['start'][11:16] if 'T' in e['start'] else '종일'
                lines.append(f"  • {time_str} {e['title']}")
        else:
            lines.append("\n📅 오늘 일정 없음")
    except Exception:
        lines.append("\n📅 일정: 조회 오류")

    # 4. 중요 메일
    try:
        mail_raw = run_skill('skills/gmail-reader/scripts/gmail_reader.py', ['--recent', '--hours', '12'])
        mails = json.loads(mail_raw)
        if mails:
            lines.append(f"\n📧 *중요 메일* ({len(mails)}건)")
            for m in mails[:3]:
                lines.append(f"  • {m['subject'][:40]}")
        else:
            lines.append("\n📧 중요 메일 없음")
    except Exception:
        lines.append("\n📧 메일: 조회 오류")

    lines.append("\n_Jarvis가 오늘도 함께합니다_ 💼")
    return '\n'.join(lines)


if __name__ == '__main__':
    msg = build_briefing()
    print(msg)
    if CHAT_ID:
        send_telegram(msg)
        print("✅ Telegram 전송 완료")
    else:
        print("⚠️ TELEGRAM_CHAT_ID 미설정. .env에 추가 필요.")
```

- [ ] **Step 2: SKILL.md 작성**

`C:\Users\Samsung\Jarvis\skills\morning-briefing\SKILL.md`:

```markdown
---
name: morning-briefing
description: 매일 오전 8시 자동으로 잔액·시장·일정·메일 브리핑을 Telegram으로 전송한다.
---

# Morning Briefing Skill

## 언제 사용하나
- 매일 08:00 자동 실행 (Windows 작업 스케줄러)
- 사용자가 "오늘 브리핑 해줘"라고 말할 때

## 사용법
```bash
python skills/morning-briefing/scripts/morning_briefing.py
```
```

- [ ] **Step 3: TELEGRAM_CHAT_ID 확인**

Telegram에서 봇에게 `/start` 전송 후 다음 URL 접속 (Bot Token 교체):
```
https://api.telegram.org/bot여기에봇토큰/getUpdates
```

JSON에서 `"chat":{"id": 숫자}` 확인 → `.env`에 추가:
```env
TELEGRAM_CHAT_ID=숫자
```

- [ ] **Step 4: 수동 실행 테스트**

```powershell
python C:\Users\Samsung\Jarvis\skills\morning-briefing\scripts\morning_briefing.py
```

Expected: 브리핑 내용 터미널 출력 + Telegram으로 메시지 수신

- [ ] **Step 5: 커밋**

```powershell
git add skills/morning-briefing/
git commit -m "feat: add morning briefing scheduler skill"
git push
```

---

## Task 15: Windows 작업 스케줄러 등록 (자동 실행)

- [ ] **Step 1: 매일 오전 8시 모닝 브리핑 등록**

관리자 권한 PowerShell에서:

```powershell
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "C:\Users\Samsung\Jarvis\skills\morning-briefing\scripts\morning_briefing.py" `
  -WorkingDirectory "C:\Users\Samsung\Jarvis"

$trigger = New-ScheduledTaskTrigger -Daily -At "08:00AM"

$settings = New-ScheduledTaskSettingsSet `
  -StartWhenAvailable `
  -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
  -TaskName "Jarvis-MorningBriefing" `
  -Action $action `
  -Trigger $trigger `
  -Settings $settings `
  -RunLevel Highest
```

- [ ] **Step 2: OpenClaw 부팅 시 자동 시작 등록**

```powershell
$action2 = New-ScheduledTaskAction `
  -Execute "openclaw" `
  -Argument "start" `
  -WorkingDirectory "C:\Users\Samsung\Jarvis"

$trigger2 = New-ScheduledTaskTrigger -AtLogOn

Register-ScheduledTask `
  -TaskName "Jarvis-OpenClaw" `
  -Action $action2 `
  -Trigger $trigger2 `
  -RunLevel Highest
```

- [ ] **Step 3: 등록 확인**

```powershell
Get-ScheduledTask -TaskName "Jarvis-MorningBriefing"
Get-ScheduledTask -TaskName "Jarvis-OpenClaw"
```

Expected: 두 작업 모두 Ready 상태

- [ ] **Step 4: 수동 실행 테스트**

```powershell
Start-ScheduledTask -TaskName "Jarvis-MorningBriefing"
```

Telegram에서 브리핑 메시지 수신 확인.

- [ ] **Step 5: 최종 커밋 및 푸시**

```powershell
cd C:\Users\Samsung\Jarvis
git add .
git commit -m "chore: finalize Jarvis multi-agent setup"
git push
```

---

## 구현 완료 체크리스트

- [ ] OpenClaw 설치 및 Telegram 봇 연결 확인
- [ ] Jarvis Core 라우팅 동작 확인
- [ ] Gmail API 인증 및 메일 읽기 확인
- [ ] Google Calendar API 인증 및 일정 조회 확인
- [ ] 개인 비서 에이전트 Telegram 응답 확인
- [ ] 네이버 금융 스크래핑 동작 확인
- [ ] 오픈뱅킹 API 연결 확인 (이용기관 등록 후)
- [ ] 금융 에이전트 Telegram 응답 확인
- [ ] GitHub 모니터 동작 확인 (유랑고)
- [ ] 개인 프로젝트 에이전트 Telegram 응답 확인
- [ ] 회사 업무 에이전트 Telegram 응답 확인
- [ ] 모닝 브리핑 Telegram 수신 확인
- [ ] Windows 작업 스케줄러 등록 확인
- [ ] PC 재부팅 후 OpenClaw 자동 시작 확인
