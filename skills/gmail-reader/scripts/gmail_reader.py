import os, sys, json, argparse, re
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly'
]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
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
    return build('gmail', 'v1', credentials=creds)


def get_recent_emails(hours=24, max_results=20):
    service = get_service()
    after = int((datetime.now() - timedelta(hours=hours)).timestamp())
    results = service.users().messages().list(
        userId='me',
        q=f'after:{after} -category:promotions -category:social',
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        detail = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        headers = {h['name']: h['value'] for h in detail['payload']['headers']}
        snippet = detail.get('snippet', '')
        emails.append({
            'id': msg['id'],
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'date': headers.get('Date', ''),
            'snippet': snippet[:200]
        })
    return emails


def get_important_emails(hours=24):
    emails = get_recent_emails(hours=hours, max_results=50)
    keywords = [
        '삼성증권', '체결', '입금', '출금', '카드', '명세서', '청구',
        '보험', '납부', '계약', '승인', '긴급', '마감', '결재',
        '국민은행', '농협', '우리은행', 'SC제일', '카카오뱅크'
    ]
    important = []
    for email in emails:
        text = email['subject'] + ' ' + email['from'] + ' ' + email['snippet']
        if any(kw in text for kw in keywords):
            email['category'] = '금융/업무'
            important.append(email)
    return important


def parse_samsung_securities(hours=48):
    service = get_service()
    after = int((datetime.now() - timedelta(hours=hours)).timestamp())
    results = service.users().messages().list(
        userId='me',
        q=f'from:삼성증권 체결 after:{after}',
        maxResults=30
    ).execute()
    trades = []
    for msg in results.get('messages', []):
        detail = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()
        snippet = detail.get('snippet', '')
        m = re.search(r'(.+?)\s+(\d+)주\s+.*?체결.*?(\d[\d,]+)원', snippet)
        if m:
            trades.append({
                'name': m.group(1).strip(),
                'quantity': int(m.group(2)),
                'price': int(m.group(3).replace(',', '')),
                'snippet': snippet[:300]
            })
    return trades


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--auth', action='store_true', help='OAuth2 초기 인증')
    parser.add_argument('--recent', action='store_true', help='최근 중요 메일 조회')
    parser.add_argument('--samsung', action='store_true', help='삼성증권 거래 파싱')
    parser.add_argument('--hours', type=int, default=24)
    args = parser.parse_args()

    if args.auth:
        get_service()
        print("인증 완료. token.json 생성됨.")
    elif args.recent:
        emails = get_important_emails(hours=args.hours)
        print(json.dumps(emails, ensure_ascii=False, indent=2))
    elif args.samsung:
        trades = parse_samsung_securities(hours=args.hours)
        print(json.dumps(trades, ensure_ascii=False, indent=2))
