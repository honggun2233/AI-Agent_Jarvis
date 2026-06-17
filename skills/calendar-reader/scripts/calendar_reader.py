import os, sys, json, argparse
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']  # 읽기+쓰기
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    from datetime import timezone
    now_local = datetime.now()
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
    utc_offset = datetime.now(timezone.utc).replace(tzinfo=None) - now_local
    start = (start_local + utc_offset).isoformat() + 'Z'
    end = (end_local + utc_offset).isoformat() + 'Z'
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
            'description': (e.get('description') or '')[:100]
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


TIMEZONE = 'Asia/Seoul'


def add_event(title, start, end=None, location='', description='', allday=False):
    """이벤트 등록. start/end는 'YYYY-MM-DDTHH:MM:SS'(시간) 또는 'YYYY-MM-DD'(종일).
    end 미지정 시 시작+1시간."""
    service = get_service()
    if allday or (len(start) == 10):
        body = {'summary': title,
                'start': {'date': start[:10]},
                'end': {'date': (end or start)[:10]}}
    else:
        if not end:
            st = datetime.fromisoformat(start)
            end = (st + timedelta(hours=1)).isoformat(timespec='seconds')
        body = {'summary': title,
                'start': {'dateTime': start, 'timeZone': TIMEZONE},
                'end': {'dateTime': end, 'timeZone': TIMEZONE}}
    if location:
        body['location'] = location
    if description:
        body['description'] = description
    created = service.events().insert(calendarId='primary', body=body).execute()
    return {'ok': True, 'id': created.get('id'),
            'title': title, 'start': start,
            'link': created.get('htmlLink', '')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auth', action='store_true')
    parser.add_argument('--today', action='store_true')
    parser.add_argument('--week', action='store_true')
    parser.add_argument('--add', action='store_true', help='이벤트 등록')
    parser.add_argument('--title', type=str)
    parser.add_argument('--start', type=str, help='YYYY-MM-DDTHH:MM:SS 또는 YYYY-MM-DD')
    parser.add_argument('--end', type=str)
    parser.add_argument('--location', type=str, default='')
    parser.add_argument('--description', type=str, default='')
    parser.add_argument('--allday', action='store_true')
    args = parser.parse_args()

    if args.auth:
        get_service()
        print("캘린더 인증 완료.")
    elif args.add:
        if not args.title or not args.start:
            print(json.dumps({'ok': False, 'error': '--title 과 --start 필수'}, ensure_ascii=False))
        else:
            print(json.dumps(add_event(args.title, args.start, args.end,
                                        args.location, args.description, args.allday),
                             ensure_ascii=False))
    elif args.today:
        print(json.dumps(get_today_events(), ensure_ascii=False, indent=2))
    elif args.week:
        print(json.dumps(get_week_events(), ensure_ascii=False, indent=2))
