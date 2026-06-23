import os, sys, json, subprocess, requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def run_skill(script_path: str, args: list) -> str:
    child_env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, script_path)] + args,
        capture_output=True, text=True, timeout=30,
        encoding='utf-8', errors='replace', env=child_env
    )
    if result.returncode != 0 and result.stderr:
        print(f"Skill error ({script_path}): {result.stderr[:200]}")
    return result.stdout.strip()


def send_telegram(message: str):
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        requests.post(url, json={
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }, timeout=10)
    except Exception as e:
        print(f"Telegram 전송 실패: {e}")


WEEKDAYS_KO = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
WEATHER_CITY = 'Seoul'

# WWO weather code → 한글 (wttr.in이 한글 번역을 제대로 안 줘서 직접 매핑)
WEATHER_KO = {
    '113': '☀️ 맑음', '116': '🌤️ 구름 조금', '119': '☁️ 흐림', '122': '☁️ 매우 흐림',
    '143': '🌫️ 안개', '248': '🌫️ 안개', '260': '🌫️ 안개',
    '176': '🌦️ 비 약간', '263': '🌦️ 약한 이슬비', '266': '🌦️ 약한 이슬비',
    '293': '🌦️ 약한 비', '296': '🌧️ 약한 비', '299': '🌧️ 비', '302': '🌧️ 비',
    '305': '🌧️ 강한 비', '308': '🌧️ 강한 비', '353': '🌦️ 소나기', '356': '🌧️ 소나기',
    '359': '🌧️ 강한 소나기', '200': '⛈️ 천둥번개', '386': '⛈️ 천둥번개', '389': '⛈️ 강한 천둥번개',
    '179': '🌨️ 눈 약간', '227': '🌨️ 눈', '230': '❄️ 폭설',
    '323': '🌨️ 약한 눈', '326': '🌨️ 약한 눈', '329': '❄️ 눈', '332': '❄️ 눈',
    '335': '❄️ 강한 눈', '338': '❄️ 폭설', '368': '🌨️ 약한 눈', '371': '❄️ 눈',
}


def get_weather() -> dict:
    """wttr.in에서 오늘 기온·강수·상태를 가져온다 (API 키 불필요)."""
    try:
        r = requests.get(f'https://wttr.in/{WEATHER_CITY}?format=j1', timeout=10)
        data = r.json()
        cur = data['current_condition'][0]
        today = data['weather'][0]
        code = cur.get('weatherCode', '')
        desc = WEATHER_KO.get(code, cur['weatherDesc'][0]['value'].strip())
        return {
            'temp': int(cur['temp_C']),
            'feels': int(cur['FeelsLikeC']),
            'desc': desc,
            'min': int(today['mintempC']),
            'max': int(today['maxtempC']),
            'rain_chance': max((int(h['chanceofrain']) for h in today['hourly']), default=0),
            'wind': int(cur.get('windspeedKmph', 0)),
            'uv': int(cur.get('uvIndex', 0)),
        }
    except Exception:
        return {}


def dress_code(w: dict) -> str:
    """기온·강수 기준 옷차림 추천."""
    if not w:
        return ''
    t = w.get('feels', w.get('temp', 15))
    if t >= 28:
        outfit = '반팔·반바지·린넨 등 얇고 시원한 옷, 자외선 차단'
    elif t >= 23:
        outfit = '반팔 / 얇은 셔츠'
    elif t >= 20:
        outfit = '긴팔 셔츠, 얇은 가디건'
    elif t >= 17:
        outfit = '맨투맨, 얇은 니트, 가디건'
    elif t >= 12:
        outfit = '자켓, 트렌치코트, 니트'
    elif t >= 9:
        outfit = '코트, 가죽자켓, 두꺼운 니트'
    elif t >= 5:
        outfit = '코트, 히트텍, 목도리'
    else:
        outfit = '패딩, 두꺼운 코트, 방한용품'
    if w.get('rain_chance', 0) >= 50:
        outfit += ' · ☔ 우산 챙기세요'
    return outfit


# 캘린더 제목에서 야외운동을 감지할 키워드
OUTDOOR_KW = ['골프', '라운딩', '라운드', '라이딩', '사이클', '자전거', '바이크',
              'golf', 'cycl', 'ride', 'riding', 'bike']


def outdoor_advice(w: dict) -> tuple:
    """야외운동 날씨 적합도 → (판정, [주의문구])."""
    if not w:
        return '정보 없음', []
    tips = []
    rc = w.get('rain_chance', 0)
    if rc >= 60:
        tips.append('☔ 비 예보')
    elif rc >= 30:
        tips.append('🌧 강수 대비')
    if w.get('wind', 0) >= 25:
        tips.append(f"💨 바람 {w['wind']}km/h")
    if w.get('uv', 0) >= 6:
        tips.append('☀️ 자외선 강(선크림)')
    if w.get('feels', 15) >= 33:
        tips.append('🥵 폭염(수분)')
    elif w.get('feels', 15) <= 2:
        tips.append('🥶 한파(방한)')
    if rc >= 60 or w.get('wind', 0) >= 30:
        verdict = '비추천 ❌'
    elif tips:
        verdict = '주의 ⚠️'
    else:
        verdict = '좋음 👍'
    return verdict, tips


def exercise_section(now, events, w) -> list:
    """오늘 운동: 평일 실내 루틴 한 줄 + 캘린더 야외운동 감지 시 날씨 적합도."""
    lines = ['\n🏃 *오늘 운동*']
    is_weekday = now.weekday() < 5
    if is_weekday:
        lines.append('  • 평일 루틴: 아침 실내 사이클 🚴 + 낮 헬스 런닝 🏃 (주 2~3회 목표)')
    # 캘린더에서 야외운동 일정 감지
    outdoor = [e for e in events
               if any(k in e.get('title', '').lower() for k in OUTDOOR_KW)]
    if outdoor:
        verdict, tips = outdoor_advice(w)
        for e in outdoor:
            t = e['start'][11:16] if 'T' in e.get('start', '') else '종일'
            title_l = e.get('title', '').lower()
            icon = '⛳' if ('골프' in title_l or 'golf' in title_l) else '🚴'
            lines.append(f"  • {icon} {e['title']} ({t}) — 야외 적합도: {verdict}")
        if tips:
            lines.append(f"    {' · '.join(tips)}")
    elif not is_weekday:
        lines.append('  • 주말 — 야외 사이클/골프 계획 있으면 일정에 등록하세요')
    return lines


def build_briefing() -> str:
    now = datetime.now()
    today = f"{now.strftime('%Y년 %m월 %d일')} {WEEKDAYS_KO[now.weekday()]}"
    lines = [f'☀️ *모닝 브리핑* — {today}\n']

    w = get_weather()
    if w:
        lines.append(
            f"*날씨:* {w['desc']} {w['temp']}°C "
            f"(체감 {w['feels']}°C, 오늘 {w['min']}~{w['max']}°C)"
        )
        lines.append(f"👔 *드레스 코드:* {dress_code(w)}")
    else:
        lines.append("🌤️ 날씨: 조회 오류")

    try:
        health = run_skill('skills/health-tracker/scripts/health_logger.py', ['--summary'])
        if health:
            lines.append(f"🩺 *건강:* {health}")
    except Exception:
        pass

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

    events = []
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
        lines.extend(exercise_section(now, events, w))
    except Exception:
        pass

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

    # 프로젝트 진척률 (project-tracker) — 신규 폴더 자동 동기화 후 진척률 표시
    try:
        lines.extend(project_section())
    except Exception:
        lines.append("\n🚀 프로젝트: 조회 오류")

    # repo 동기화 상태 (GitHub SSOT vs 로컬) — 문제 있는 repo만 표시
    try:
        sync = run_skill('skills/repo-sync/scripts/repo_sync_status.py', [])
        if sync:
            if sync.startswith('✅'):
                lines.append(f"\n🔄 *Repo 동기화:* {sync}")
            else:
                lines.append("\n🔄 *Repo 동기화 주의:*")
                for s in sync.splitlines():
                    lines.append(f"  {s}")
    except Exception:
        pass

    lines.append("\n_Jarvis가 오늘도 함께합니다_ 💼")
    return '\n'.join(lines)


def _bar(pct, width=10):
    filled = round(pct * width / 100)
    return '█' * filled + '░' * (width - filled)


def project_section():
    """project-tracker 진척률 섹션. 신규 폴더 동기화 → 진척률/추출대기 표시."""
    out = []
    # 1) 신규 폴더 동기화 (토큰 0). 이번에 새로 만든 pending 폴더명만 반환.
    new_raw = run_skill('skills/project-tracker/scripts/project_scan.py', ['--report'])
    new_folders = [l.strip() for l in new_raw.splitlines() if l.strip()]

    data = json.loads(run_skill('skills/project-tracker/scripts/project_tracker.py', ['--json']) or '[]')
    if not data:
        return out

    # 최근 활동(🔥) 보조 신호: work-status에서 24h 내 변경된 프로젝트명 집합
    active_names = set()
    try:
        work = json.loads(run_skill('skills/work-status/scripts/work_status.py', ['--work']) or '[]')
        active_names = {w['name'] for w in work if w.get('exists') and w.get('recent_count')}
    except Exception:
        pass

    def fire(p):
        return ' 🔥' if any(n in p['name'] or p['name'] in n or n in p['folder'] for n in active_names) else ''

    def render(items):
        rows = []
        for p in sorted(items, key=lambda x: (x['status'] == 'pending', -x['pct'])):
            if p['status'] == 'pending':
                continue
            cnt = f" [{p['done']}/{p['total']}]" if p['total'] else ''
            rows.append(f"  {_bar(p['pct'])} {p['pct']:3d}%  {p['name']}{cnt}{fire(p)}")
        return rows

    personal = [p for p in data if p['type'] == 'personal']
    work = [p for p in data if p['type'] == 'work']
    other = [p for p in data if p['type'] not in ('personal', 'work')]

    if personal:
        lines_p = render(personal)
        if lines_p:
            out.append("\n🚀 *개인 프로젝트*")
            out.extend(lines_p)
    if work:
        lines_w = render(work)
        if lines_w:
            out.append("\n💼 *회사 업무*")
            out.extend(lines_w)
    if other:
        lines_o = render(other)
        if lines_o:
            out.append("\n· *기타*")
            out.extend(lines_o)

    # 추출 대기(마일스톤 미등록) 안내
    pending = [p['name'] for p in data if p['status'] == 'pending']
    if pending:
        head = "🆕 새 프로젝트" if new_folders else "⏳ 마일스톤 추출 대기"
        sample = ', '.join(pending[:6]) + (' 외' if len(pending) > 6 else '')
        out.append(f"\n{head} {len(pending)}개 — {sample}")
    return out


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    msg = build_briefing()
    try:
        print(msg)
    except Exception:
        pass
    if CHAT_ID:
        send_telegram(msg)
        print("✅ Telegram 전송 완료")
    else:
        print("⚠️ TELEGRAM_CHAT_ID 미설정. .env에 추가 필요.")
