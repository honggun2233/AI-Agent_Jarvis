"""실시간 중요 메일 알림.

cron(작업 스케줄러)으로 20분마다 실행. 새로 도착한 중요 메일을 즉시 텔레그램으로.
- 운영 시간: 08:00~22:00 (야간 제외)
- 중복 방지: data/alerted_emails.json 에 알린 메일 id 기록
- 중요 키워드 판정은 gmail-reader의 get_important_emails 재사용
"""
import os, sys, json
from datetime import datetime
import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
load_dotenv(os.path.join(BASE_DIR, '.env'))
sys.path.insert(0, os.path.join(BASE_DIR, 'skills', 'gmail-reader', 'scripts'))
from gmail_reader import get_important_emails

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
STATE_PATH = os.path.join(BASE_DIR, 'data', 'alerted_emails.json')

# 운영 시간 (이 시간대에만 알림)
ACTIVE_START = 8
ACTIVE_END = 22


def load_state():
    try:
        with open(STATE_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'alerted_ids': []}


def save_state(state):
    # 무한 증가 방지: 최근 500개만 유지
    state['alerted_ids'] = state['alerted_ids'][-500:]
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


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


def clean_from(raw: str) -> str:
    # "우리카드" <wooricard@...> → 우리카드
    if '<' in raw:
        name = raw.split('<')[0].strip().strip('"')
        return name or raw
    return raw


def main(force=False):
    now = datetime.now()
    if not force and not (ACTIVE_START <= now.hour < ACTIVE_END):
        print(f"운영 시간 외 ({now.hour}시) — 건너뜀")
        return

    state = load_state()
    seen = set(state['alerted_ids'])

    # 최근 1시간 내 중요 메일 (20분 주기라 1h 윈도면 충분히 겹침)
    emails = get_important_emails(hours=1)
    new_mails = [e for e in emails if e['id'] not in seen]

    if not new_mails:
        print(f"[{now:%H:%M}] 새 중요 메일 없음")
        return

    for e in new_mails:
        sender = clean_from(e.get('from', ''))
        subject = e.get('subject', '(제목 없음)')
        snippet = e.get('snippet', '')[:120]
        msg = (
            f"🔔 *중요 메일 도착*\n"
            f"보낸이: {sender}\n"
            f"제목: {subject}\n\n"
            f"_{snippet}_"
        )
        if send_telegram(msg):
            seen.add(e['id'])
            print(f"  알림 전송: {subject[:40]}")

    state['alerted_ids'] = list(seen)
    save_state(state)
    print(f"[{now:%H:%M}] {len(new_mails)}건 알림 완료")


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    force = '--force' in sys.argv
    main(force=force)
