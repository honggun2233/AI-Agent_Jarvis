import sys, json, argparse, requests
from bs4 import BeautifulSoup

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def get_stock_price(ticker: str) -> dict:
    url = f'https://finance.naver.com/item/main.naver?code={ticker}'
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    price_tag = soup.select_one('#chart_area .blind')
    name_tag = soup.select_one('.wrap_company h2 a')
    change_tag = soup.select_one('.rate_info .blind')
    return {
        'ticker': ticker,
        'name': name_tag.text.strip() if name_tag else ticker,
        'price': price_tag.text.strip() if price_tag else 'N/A',
        'change': change_tag.text.strip() if change_tag else 'N/A'
    }


def get_market_summary() -> dict:
    url = 'https://finance.naver.com/'
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    result = {}
    kospi = soup.select_one('.kospi_area .num')
    kosdaq = soup.select_one('.kosdaq_area .num')
    if kospi:
        result['코스피'] = kospi.text.strip()
    if kosdaq:
        result['코스닥'] = kosdaq.text.strip()
    return result


def get_portfolio_value(holdings: list) -> list:
    result = []
    for h in holdings:
        info = get_stock_price(h['ticker'])
        try:
            price_num = int(info['price'].replace(',', '').replace('원', ''))
            value = price_num * h['quantity']
            info['quantity'] = h['quantity']
            info['value'] = value
            info['value_str'] = f"{value:,}원"
        except Exception:
            info['quantity'] = h['quantity']
            info['value'] = 0
            info['value_str'] = '계산 불가'
        result.append(info)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--market', action='store_true', help='시장 지수 현황')
    parser.add_argument('--stock', type=str, help='종목코드 현재가 조회')
    parser.add_argument('--portfolio', type=str, help='포트폴리오 JSON')
    args = parser.parse_args()

    if args.market:
        print(json.dumps(get_market_summary(), ensure_ascii=False, indent=2))
    elif args.stock:
        print(json.dumps(get_stock_price(args.stock), ensure_ascii=False, indent=2))
    elif args.portfolio:
        holdings = json.loads(args.portfolio)
        print(json.dumps(get_portfolio_value(holdings), ensure_ascii=False, indent=2))
