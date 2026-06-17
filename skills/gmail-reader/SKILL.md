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
