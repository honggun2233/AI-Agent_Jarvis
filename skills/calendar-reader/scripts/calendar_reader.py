import os, sys, json, argparse
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    import time
    # Use local date for start/end to correctly capture KST events
    now_local = datetime.now()
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
    # Convert to UTC for API
    utc_offset = datetime.utcnow() - now_local
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auth', action='store_true')
    parser.add_argument('--today', action='store_true')
    parser.add_argument('--week', action='store_true')
    args = parser.parse_args()

    if args.auth:
        get_service()
        print("캘린더 인증 완료.")
    elif args.today:
        print(json.dumps(get_today_events(), ensure_ascii=False, indent=2))
    elif args.week:
        print(json.dumps(get_week_events(), ensure_ascii=False, indent=2))
