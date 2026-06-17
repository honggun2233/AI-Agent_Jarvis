---
name: open-banking
description: 금융결제원 오픈뱅킹 API로 농협·우리·SC·카카오 계좌 잔액과 거래내역을 조회한다.
---

# Open Banking Skill

## 언제 사용하나
- 잔액, 통장, 은행 잔고를 물어볼 때
- 최근 지출 내역이 필요할 때

## 사전 조건
KFTC_ACCESS_TOKEN, KFTC_USER_SEQ_NO가 .env에 설정되어 있어야 함.
오픈뱅킹 이용기관 등록 필요 (developers.kftc.or.kr).

## 사용법

전체 잔액:
```bash
python skills/open-banking/scripts/open_banking.py --balances
```

거래내역:
```bash
python skills/open-banking/scripts/open_banking.py --txn FINTECH_USE_NUM --days 7
```
