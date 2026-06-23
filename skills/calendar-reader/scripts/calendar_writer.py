import os, sys, json, argparse, re
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TOKEN_PATH = os.path.join(BASE_DIR, 'token_calendar.json')
CREDS_PATH = os.path.join(BASE_DIR, 'credentials.json')
TZ = 'Asia/Seoul'

# Google Calendar colorId: 11=토마토(빨강) 10=바질(초록) 3=포도(보라)
COLOR_MAP = {'work': '11', 'exercise': '10', 'drinks': '3'}

KW_EXERCISE = ['자전거', '사이클', '라이딩', '골프', '등산', '하이킹', '러닝', '런닝', '달리기',
               '크로스핏', '그란폰도', '라운딩', '파크골프', '운동', '헬스', '마라톤', '개달려']
KW_DRINKS = ['술자리', '술집', '회식', '한잔', '맥주', '소주', '와인', '막걸리', '뒷풀이', '뒤풀이', '호프', '포차', '한잔하', '음주']
KW_WORK = ['회의', '미팅', '보고', '품의', '주간', '면담', '결재', '상무', '대표', '부장', '팀장',
           '업무', '컨퍼런스', 'kickoff', '리뷰', '점검', '분석', 'meeting', '발표', '세미나']


def classify(title):
    t = (title or '').lower()
    for kw in KW_DRINKS:
        if kw.lower() in t:
            return 'drinks'
    for kw in KW_EXERCISE:
        if kw.lower() in t:
            return 'exercise'
    for kw in KW_WORK:
        if kw.lower() in t:
            return 'work'
    return None


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


def resolve_color(color, title):
    if color in COLOR_MAP:
        return COLOR_MAP[color]
    if color and color.isdigit():
        return color
    cat = classify(title)
    return COLOR_MAP.get(cat)


def add_event(title, start_iso, duration_min=60, location='', description='', color=None):
    service = get_service()
    start_dt = datetime.fromisoformat(start_iso)
    end_dt = start_dt + timedelta(minutes=duration_min)
    body = {
        'summary': title, 'location': location, 'description': description,
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': TZ},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': TZ},
    }
    cid = resolve_color(color, title)
    if cid:
        body['colorId'] = cid
    ev = service.events().insert(calendarId='primary', body=body).execute()
    return {'id': ev.get('id'), 'htmlLink': ev.get('htmlLink'), 'summary': ev.get('summary'),
            'start': ev['start'].get('dateTime'), 'colorId': ev.get('colorId')}


def colorize_upcoming(days=120):
    service = get_service()
    now = datetime.utcnow()
    res = service.events().list(calendarId='primary', timeMin=now.isoformat() + 'Z',
                                timeMax=(now + timedelta(days=days)).isoformat() + 'Z',
                                singleEvents=True, orderBy='startTime', maxResults=250).execute()
    changed = []
    for e in res.get('items', []):
        cat = classify(e.get('summary', ''))
        if not cat:
            continue
        want = COLOR_MAP[cat]
        if e.get('colorId') == want:
            continue
        service.events().patch(calendarId='primary', eventId=e['id'], body={'colorId': want}).execute()
        changed.append({'title': e.get('summary'), 'cat': cat, 'color': want})
    return changed


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--title')
    p.add_argument('--start', help='ISO local, e.g. 2026-06-29T19:00:00')
    p.add_argument('--duration', type=int, default=60)
    p.add_argument('--location', default='')
    p.add_argument('--description', default='')
    p.add_argument('--color', default=None, help='work|exercise|drinks|<colorId>')
    p.add_argument('--colorize', action='store_true', help='기존 다가오는 일정 일괄 색칠')
    a = p.parse_args()
    if a.colorize:
        out = colorize_upcoming()
        print(json.dumps({'recolored': out, 'count': len(out)}, ensure_ascii=False))
    else:
        out = add_event(a.title, a.start, a.duration, a.location, a.description, a.color)
        print(json.dumps(out, ensure_ascii=False))
