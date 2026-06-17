"""금융 추적: 카드 결제일 마감 리마인더 + 메일 기반 지출 보조 집계.

한계(중요):
- 우리/삼성카드 이용대금명세서는 '암호화 보안메일'이라 본문에 금액이 없음.
  → 카드 '결제일'은 제목에서 추출 가능 → 마감 리마인더는 정확히 동작.
  → 카드 '총 청구액'은 메일로 못 가져옴 (앱에서 직접 확인 필요).
- --expenses 는 본문에 금액이 노출되는 영수증/구독 메일(Apple, Google Play 등)만
  잡아 '부분 합계'를 냄. 전체 지출이 아님.

사용:
  python finance_tracker.py --deadlines          # 결제일 3일 전 리마인더 (작업 스케줄러용)
  python finance_tracker.py --deadlines --force  # 시간/중복 무시 강제 출력
  python finance_tracker.py --expenses           # 이번 달 메일에서 잡힌 결제 목록·합계
  python finance_tracker.py --expenses --month 2026-05
"""
import os, sys, json, re, base64, argparse
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(BASE_DIR, '.env'))
sys.path.insert(0, os.path.join(BASE_DIR, 'skills', 'gmail-reader', 'scripts'))
from gmail_reader import get_service

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
STATE_PATH = os.path.join(BASE_DIR, 'data', 'finance_alerts.json')

DEADLINE_NOTICE_DAYS = 3  # 결제일 N일 전부터 알림


def send_telegram(message: str):
    if not (BOT_TOKEN and CHAT_ID):
        print("TELEGRAM 미설정")
        return False
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        r = requests.post(url, json={
            'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown',
            'disable_web_page_preview': True,
        }, timeout=10)
        return r.ok
    except Exception as e:
        print(f"Telegram 전송 실패: {e}")
        return False


def load_state():
    try:
        with open(STATE_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'notified_deadlines': []}


def save_state(state):
    state['notified_deadlines'] = state['notified_deadlines'][-200:]
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def clean_from(raw: str) -> str:
    if '<' in raw:
        return (raw.split('<')[0].strip().strip('"')) or raw
    return raw


# ---------- 결제일 마감 리마인더 ----------

def find_card_deadlines(days_back=45):
    """카드 이용대금명세서 메일 제목에서 (카드명, 결제일 date)를 추출."""
    service = get_service()
    after = int((datetime.now() - timedelta(days=days_back)).timestamp())
    q = f'after:{after} (이용대금명세서 OR 결제일 OR 청구서)'
    res = service.users().messages().list(userId='me', q=q, maxResults=40).execute()
    found = {}  # key=(card, date) → dict
    for m in res.get('messages', []):
        d = service.users().messages().get(
            userId='me', id=m['id'], format='metadata',
            metadataHeaders=['From', 'Subject']).execute()
        headers = {h['name']: h['value'] for h in d['payload']['headers']}
        subj = headers.get('Subject', '')
        sender = clean_from(headers.get('From', ''))
        # 2026년06월25일(결제일)
        mm = re.search(r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*\(?\s*결제일', subj)
        if not mm:
            continue
        y, mo, da = int(mm.group(1)), int(mm.group(2)), int(mm.group(3))
        try:
            due = datetime(y, mo, da)
        except ValueError:
            continue
        # 카드사명 추정
        card = '카드'
        cm = re.search(r'\[([^\]]+카드)\]', subj) or re.search(r'(\S+카드)', sender)
        if cm:
            card = cm.group(1)
        found[(card, due.date().isoformat())] = {'card': card, 'due': due, 'subject': subj}
    return list(found.values())


def deadlines(force=False):
    state = load_state()
    notified = set(state['notified_deadlines'])
    today = datetime.now().date()

    items = find_card_deadlines()
    alerts = []
    for it in items:
        due_date = it['due'].date()
        delta = (due_date - today).days
        key = f"{it['card']}-{due_date.isoformat()}"
        if 0 <= delta <= DEADLINE_NOTICE_DAYS:
            if force or key not in notified:
                alerts.append((it, delta, key))

    if not alerts:
        print(f"[{today}] {DEADLINE_NOTICE_DAYS}일 내 카드 결제 마감 없음")
        return

    lines = ["💳 *카드 결제 마감 임박*\n"]
    for it, delta, key in sorted(alerts, key=lambda x: x[1]):
        when = "오늘" if delta == 0 else f"{delta}일 후"
        lines.append(f"• {it['card']}: {it['due']:%m월 %d일}({when}) 결제 예정")
        notified.add(key)
    lines.append("\n_금액은 카드사 앱에서 확인하세요 (명세서가 보안메일이라 자동조회 불가)_")
    msg = '\n'.join(lines)

    if send_telegram(msg):
        state['notified_deadlines'] = list(notified)
        save_state(state)
        print(f"[{today}] 마감 리마인더 {len(alerts)}건 전송")
    print(msg)


# ---------- 메일 기반 지출 보조 집계 ----------

RECEIPT_KEYWORDS = ['영수증', 'receipt', '결제', '구독', '청구', 'invoice', 'payment', '주문']


def _extract_body(payload):
    texts = []
    if payload.get('body', {}).get('data'):
        try:
            raw = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', 'replace')
            texts.append(raw)
        except Exception:
            pass
    for p in payload.get('parts', []) or []:
        texts.extend(_extract_body(p))
    return '\n'.join(texts)


def _plausible_amounts(text):
    amounts = []
    for m in re.finditer(r'₩\s?([\d,]{2,})', text):
        amounts.append(int(m.group(1).replace(',', '')))
    for m in re.finditer(r'([\d,]{4,})\s*원', text):
        amounts.append(int(m.group(1).replace(',', '')))
    return [a for a in amounts if 1000 <= a <= 100_000_000]


def expenses(month=None):
    service = get_service()
    if month:
        y, mo = map(int, month.split('-'))
    else:
        now = datetime.now()
        y, mo = now.year, now.month
    start = datetime(y, mo, 1)
    end = datetime(y + (mo == 12), (mo % 12) + 1, 1)
    after = int(start.timestamp())
    before = int(end.timestamp())

    kw = ' OR '.join(RECEIPT_KEYWORDS)
    q = f'after:{after} before:{before} ({kw})'
    res = service.users().messages().list(userId='me', q=q, maxResults=60).execute()

    items = []
    for m in res.get('messages', []):
        d = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
        headers = {h['name']: h['value'] for h in d['payload']['headers']}
        subj = headers.get('Subject', '')
        sender = clean_from(headers.get('From', ''))
        body = _extract_body(d['payload'])
        amts = _plausible_amounts(body + ' ' + subj)
        if not amts:
            continue
        charge = max(amts)  # 영수증 내 최댓값을 청구액으로 추정
        items.append({'sender': sender, 'subject': subj[:50], 'amount': charge})

    # 중복 제거: 같은 보낸이+금액은 1건으로 (주문 1건이 메일 여러 통 오는 경우 방지)
    deduped = {}
    for it in items:
        deduped[(it['sender'], it['amount'])] = it
    items = list(deduped.values())

    total = sum(i['amount'] for i in items)
    result = {
        'month': f'{y}-{mo:02d}',
        'count': len(items),
        'total_detected': total,
        'items': sorted(items, key=lambda x: -x['amount']),
        'note': '메일 본문에 금액이 노출된 결제만 집계한 부분 합계. 카드 명세서(보안메일)는 미포함.'
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument('--deadlines', action='store_true')
    ap.add_argument('--expenses', action='store_true')
    ap.add_argument('--month', type=str, default=None)
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    if args.deadlines:
        deadlines(force=args.force)
    elif args.expenses:
        expenses(month=args.month)
    else:
        print("--deadlines 또는 --expenses 를 지정하세요")
