import os, sys, json, argparse, requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

BASE_URL = 'https://openapi.kftc.or.kr/v2.0'
ACCESS_TOKEN = os.getenv('KFTC_ACCESS_TOKEN', '')
USER_SEQ_NO = os.getenv('KFTC_USER_SEQ_NO', '')

HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

BANK_NAMES = {
    '011': '농협', '020': '우리', '023': 'SC제일', '090': '카카오뱅크'
}


def get_accounts() -> list:
    resp = requests.get(
        f'{BASE_URL}/user/me',
        headers=HEADERS,
        params={'user_seq_no': USER_SEQ_NO}
    )
    data = resp.json()
    accounts = data.get('res_list', [])
    return [{
        'bank': BANK_NAMES.get(a.get('fintech_use_num', '')[:3], a.get('bank_code_std', '')),
        'account': a.get('account_num_masked', ''),
        'fintech_use_num': a.get('fintech_use_num', '')
    } for a in accounts]


def get_balance(fintech_use_num: str) -> dict:
    import datetime
    resp = requests.get(
        f'{BASE_URL}/account/balance/fin_num',
        headers=HEADERS,
        params={
            'fintech_use_num': fintech_use_num,
            'tran_dtime': datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        }
    )
    data = resp.json()
    return {
        'balance': data.get('balance_amt', '0'),
        'available': data.get('available_amt', '0'),
        'currency': data.get('currency_code', 'KRW')
    }


def get_all_balances() -> list:
    accounts = get_accounts()
    result = []
    total = 0
    for acc in accounts:
        bal = get_balance(acc['fintech_use_num'])
        amount = int(bal['balance'].replace(',', ''))
        total += amount
        result.append({
            'bank': acc['bank'],
            'account': acc['account'],
            'balance': f"{amount:,}원"
        })
    result.append({'bank': '합계', 'account': '-', 'balance': f"{total:,}원"})
    return result


def get_transactions(fintech_use_num: str, days: int = 7) -> list:
    from datetime import datetime, timedelta
    now = datetime.now()
    start = (now - timedelta(days=days)).strftime('%Y%m%d')
    end = now.strftime('%Y%m%d')
    resp = requests.get(
        f'{BASE_URL}/account/transaction_list/fin_num',
        headers=HEADERS,
        params={
            'fintech_use_num': fintech_use_num,
            'inquiry_type': 'A',
            'inquiry_base': 'D',
            'from_date': start,
            'to_date': end,
            'sort_order': 'D',
            'tran_dtime': now.strftime('%Y%m%d%H%M%S')
        }
    )
    data = resp.json()
    txns = data.get('res_list', [])
    return [{
        'date': t.get('tran_date', ''),
        'type': '입금' if t.get('inout_type') == 'I' else '출금',
        'amount': t.get('tran_amt', '0') + '원',
        'balance': t.get('after_balance_amt', '0') + '원',
        'memo': t.get('print_content', '')
    } for t in txns[:20]]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--balances', action='store_true', help='전체 잔액')
    parser.add_argument('--txn', type=str, help='거래내역 (fintech_use_num)')
    parser.add_argument('--days', type=int, default=7)
    args = parser.parse_args()

    if args.balances:
        print(json.dumps(get_all_balances(), ensure_ascii=False, indent=2))
    elif args.txn:
        print(json.dumps(get_transactions(args.txn, args.days), ensure_ascii=False, indent=2))
