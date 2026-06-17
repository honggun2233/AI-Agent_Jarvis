# Jarvis 멀티에이전트 시스템 설계

**날짜:** 2026-06-17  
**플랫폼:** OpenClaw (자가 호스팅)  
**인터페이스:** Telegram Bot  
**실행 환경:** Windows 11 홈 PC (C:\Users\Samsung\Jarvis)  
**AI 모델:** Claude API (claude-opus-4-8)

---

## 1. 시스템 개요

OpenClaw Gateway 위에 5개의 전문 에이전트를 구성하고, 하나의 Telegram 봇으로 통합 접근한다. Jarvis Core가 모든 메시지를 수신해 의도를 파악하고 적절한 전문 에이전트로 라우팅한다. 에이전트는 반응형(사용자 요청)과 능동형(자동 알림) 두 가지 모드로 동작한다.

---

## 2. 디렉터리 구조

```
C:\Users\Samsung\Jarvis\
├── openclaw.json              # OpenClaw Gateway 설정
├── agents/
│   ├── core/
│   │   └── SOUL.md            # 총괄 오케스트레이터
│   ├── finance/
│   │   └── SOUL.md            # 금융 관리
│   ├── assistant/
│   │   └── SOUL.md            # 개인 비서
│   ├── work/
│   │   └── SOUL.md            # 회사 업무
│   └── project/
│       └── SOUL.md            # 개인 프로젝트
├── skills/
│   ├── open_banking.py        # 오픈뱅킹 API 클라이언트
│   ├── gmail_parser.py        # Gmail API + 삼성증권 파싱
│   ├── naver_finance.py       # 네이버 금융 스크래핑
│   └── github_monitor.py     # GitHub API 클라이언트
├── data/
│   ├── finance.md             # 수동 보완 금융 데이터
│   ├── tasks.md               # 할일 목록
│   └── projects.md            # 프로젝트 현황 메모
└── docs/
    └── superpowers/specs/
        └── 2026-06-17-jarvis-multiagent-design.md
```

---

## 3. 에이전트 상세 설계

### 3-1. Jarvis Core (총괄 오케스트레이터)

**역할:** 모든 Telegram 메시지의 진입점. 의도 분류 후 전문 에이전트로 핸드오프.

**라우팅 규칙:**
- "잔액", "지출", "ETF", "주식", "카드", "보험" → finance-agent
- "메일", "일정", "할일", "검색", "알려줘" → assistant-agent
- "회사", "프로젝트", "업무", "ETF 개발" → work-agent
- "유랑고", "온기로", "GitHub", "배포" → project-agent

**자동 스케줄:**
- 매일 08:00 — 모닝 브리핑 (잔액·ETF 수익률·오늘 일정·중요 메일)
- 매주 월요일 09:00 — 주간 지출 리포트 + 프로젝트 주간 요약

**SOUL.md 핵심 지침:**
- 항상 한국어로 답변
- 라우팅 결과를 사용자에게 노출하지 않고 자연스럽게 통합 응답
- 모호한 요청은 먼저 명확히 물어보고 처리

---

### 3-2. 금융 관리 에이전트 (finance-agent)

**데이터 소스:**

| 소스 | 연계 방식 | 제공 데이터 |
|------|-----------|-------------|
| 오픈뱅킹 (금융결제원) | REST API | 농협·우리·SC·카카오 잔액·거래내역 |
| Gmail API | IMAP + Gmail API | 삼성증권 거래체결 메일 파싱 |
| 네이버 금융 | HTTP 스크래핑 | 보유 ETF 현재가·지수·뉴스 |
| Gmail API | 이메일 파싱 | 카드 명세서·보험료 청구서 |

**핵심 기능:**
- 전 은행 잔액 합산 및 은행별 최근 거래내역 조회
- 삼성증권 거래체결 이메일 파싱 → 포트폴리오 재구성
- ETF 보유 수량 × 현재가 = 실시간 평가금액 계산
- 월별 지출 카테고리 분류 (식비·교통·보험·투자 등)

**자동 알림 트리거:**
- 카드 결제 이메일 도착 즉시 → Telegram 알림
- ETF 등락 5% 초과 → 즉시 알림
- 카드값·보험료 납부일 D-3 → 사전 알림
- 월 예산 80% 도달 → 경고 알림

---

### 3-3. 개인 비서 에이전트 (assistant-agent)

**데이터 소스:**
- Gmail API: 전체 받은편지함 모니터링
- Google Calendar API: 일정 조회·생성
- 웹 검색: OpenClaw 내장 검색 스킬

**핵심 기능:**
- 중요 메일 실시간 감지 (금융·업무·개인 카테고리 분류)
- 메일 3줄 요약 후 Telegram 전송
- 답장 필요 메일 플래그 관리
- 오늘/이번 주 일정 조회 및 알림
- 자연어로 할일 추가·완료 처리

**중요 메일 판단 기준:**
- 발신자: 회사 도메인, 주요 거래처, 금융기관
- 키워드: 계약, 마감, 긴급, 결제, 승인, 검토 요청

---

### 3-4. 회사 업무 에이전트 (work-agent)

**데이터 소스:**
- 파일시스템: `C:\project\` 내 회사 프로젝트 폴더
- 파일시스템: `C:\etfdev\` ETF 운용 시스템

**모니터링 대상 프로젝트:**
- ETF 상품 개발 프로젝트
- ETF 운용 시스템 개발 project
- ETF 지수 DATA 관리 project
- AI 포털 마이그레이션 프로젝트
- 문서관리 솔루션 프로젝트
- 기타 `C:\project\` 내 폴더

**핵심 기능:**
- 프로젝트 폴더별 최근 수정 파일 추적
- `data\projects.md` 기반 업무 현황 요약
- "오늘 뭐 해야 해?" → 진행 중 프로젝트 우선순위 정리
- 주간 업무 요약 리포트

---

### 3-5. 개인 프로젝트 에이전트 (project-agent)

**데이터 소스:**
- GitHub API: `honggun2233/urango1` 레포
- GitHub API: 온기로 레포 (확인 필요)
- Vercel API: 유랑고 배포 현황 (`vercel.json` 존재 확인)
- 파일시스템: `C:\project\urango_project\`, `C:\project\ongiro 프로젝트\`

**핵심 기능:**

*유랑고 (URANGO):*
- 오픈 Issues·PR 수 및 목록 조회
- 최근 커밋 활동 요약
- Vercel 배포 상태 확인
- "유랑고 지금 어때?" 한마디로 전체 현황 파악

*온기로 (Ongiro):*
- 개발 진행 현황 (파일 수정 이력 기반)
- 앱·웹 빌드 상태
- 주요 기능 개발 체크리스트 관리

**자동 알림 트리거:**
- 새 GitHub Issue/PR 오픈 → 즉시 Telegram 알림
- Vercel 배포 성공/실패 → 결과 알림

---

## 4. OpenClaw 설정 (openclaw.json 구조)

```json
{
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
    { "id": "core",      "name": "Jarvis Core",      "soul": "agents/core/SOUL.md",      "channels": ["telegram"] },
    { "id": "finance",   "name": "Finance Agent",    "soul": "agents/finance/SOUL.md",   "channels": [] },
    { "id": "assistant", "name": "Assistant Agent",  "soul": "agents/assistant/SOUL.md", "channels": [] },
    { "id": "work",      "name": "Work Agent",       "soul": "agents/work/SOUL.md",      "channels": [] },
    { "id": "project",   "name": "Project Agent",    "soul": "agents/project/SOUL.md",   "channels": [] }
  ]
}
```

---

## 5. 외부 API 키 목록

구현 전 준비 필요:

| 서비스 | 발급처 | 용도 |
|--------|--------|------|
| Anthropic API Key | console.anthropic.com | Claude 모델 호출 |
| Telegram Bot Token | @BotFather | Telegram 봇 생성 |
| 오픈뱅킹 이용기관 코드 | developers.kftc.or.kr | 은행 계좌 연동 |
| Gmail OAuth2 Client | Google Cloud Console | Gmail 읽기 권한 |
| Google Calendar API | Google Cloud Console | 일정 조회·생성 |
| GitHub Personal Access Token | github.com/settings/tokens | 레포 이슈·PR 조회 |
| Vercel API Token | vercel.com/account/tokens | 배포 상태 조회 |

---

## 6. 구현 단계 (우선순위 순)

1. **OpenClaw 설치 및 Telegram 봇 연결** — 가장 먼저, 동작 확인
2. **Jarvis Core SOUL.md** — 라우팅 기본 동작
3. **개인 비서 에이전트** — Gmail + Calendar (즉시 체감 가능)
4. **금융 에이전트** — 오픈뱅킹 + Gmail 파싱
5. **개인 프로젝트 에이전트** — GitHub + Vercel
6. **회사 업무 에이전트** — 파일시스템 기반
7. **자동 스케줄러** — 모닝 브리핑 + 알림

---

## 7. 제약 사항

- 삼성증권: 공개 API 없음 → Gmail 파싱으로 대체 (거래체결 이메일 필수 수신 설정)
- 오픈뱅킹: 개인 이용기관 등록 절차 필요 (1~2주 소요 가능)
- 집 PC: 24시간 켜두거나 Windows 작업 스케줄러로 절전 방지 설정 필요
- 보험: 별도 API 없음 → 보험사 이메일 파싱으로 납부일·금액 추적
