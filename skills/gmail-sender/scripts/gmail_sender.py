import os, sys, json, base64, argparse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# token.json 을 gmail-reader 와 공유한다. 두 스코프가 한 토큰에 함께 부여돼야 하므로
# 양쪽 SCOPES 를 동일하게 유지할 것.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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


def send_email(to, subject, body, cc=None, bcc=None, html=False):
    service = get_service()
    if html:
        msg = MIMEMultipart('alternative')
        msg.attach(MIMEText(body, 'html', _charset='utf-8'))
    else:
        msg = MIMEText(body, 'plain', _charset='utf-8')
    msg['to'] = to
    msg['subject'] = subject
    if cc:
        msg['cc'] = cc
    if bcc:
        msg['bcc'] = bcc
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(
        userId='me', body={'raw': raw}
    ).execute()
    return sent


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gmail 발송')
    parser.add_argument('--auth', action='store_true', help='OAuth2 인증(브라우저)')
    parser.add_argument('--to', help='수신자 이메일')
    parser.add_argument('--subject', help='제목')
    parser.add_argument('--body', help='본문 텍스트')
    parser.add_argument('--body-file', help='본문을 읽어올 파일 경로(UTF-8)')
    parser.add_argument('--cc')
    parser.add_argument('--bcc')
    parser.add_argument('--html', action='store_true', help='본문을 HTML로 발송')
    args = parser.parse_args()

    if args.auth:
        get_service()
        print('인증 완료. token.json 생성됨.')
        sys.exit(0)

    if not args.to or not args.subject:
        print('오류: --to 와 --subject 는 필수입니다.', file=sys.stderr)
        sys.exit(1)

    body = args.body
    if args.body_file:
        with open(args.body_file, 'r', encoding='utf-8') as f:
            body = f.read()
    if body is None:
        print('오류: --body 또는 --body-file 중 하나가 필요합니다.', file=sys.stderr)
        sys.exit(1)

    sent = send_email(args.to, args.subject, body,
                      cc=args.cc, bcc=args.bcc, html=args.html)
    print(json.dumps({'status': 'sent', 'id': sent.get('id'),
                      'to': args.to, 'subject': args.subject},
                     ensure_ascii=False))
