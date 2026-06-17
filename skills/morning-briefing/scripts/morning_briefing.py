import os, sys, json, subprocess, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
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

    try:
        bal_raw = run_skill('skills/open-banking/scripts/open_banking.py', ['--balances'])
        balances = json.loads(bal_raw)
        total = next((b for b in balances if b['bank'] == '합계'), None)
        if total:
            lines.append(f"💰 *총 잔액:* {total['balance']}")
    except Exception:
        lines.append("💰 잔액: 조회 오류")

    try:
        market_raw = run_skill('skills/naver-finance/scripts/naver_finance.py', ['--market'])
        market = json.loads(market_raw)
        kospi = market.get('코스피', 'N/A')
        kosdaq = market.get('코스닥', 'N/A')
        lines.append(f"📈 *시장:* 코스피 {kospi} / 코스닥 {kosdaq}")
    except Exception:
        lines.append("📈 시장: 조회 오류")

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
