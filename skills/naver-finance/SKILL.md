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
