"""health_logger.py — 텔레그램/채팅으로 받은 건강 수치를 파싱·저장하고, 추세를 조회한다.

사용법:
  # 기록 (자유 형식 한국어 텍스트를 그대로 넘김)
  python health_logger.py --log "체중 78.2 공복혈당 105 혈압 120/80"
  # 최근값 + 추세 요약 (모닝 브리핑이 호출)
  python health_logger.py --summary
  # 원시 로그 확인
  python health_logger.py --dump

데이터: Jarvis/data/health_log.jsonl  (한 줄당 한 측정값)
"""
import os, sys, json, re, argparse
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data')
LOG_PATH = os.path.join(DATA_DIR, 'health_log.jsonl')

# metric 정의: key → (표시명, 단위, 정규식 키워드)
METRICS = {
    'weight':         ('체중', 'kg', r'(?:체중|몸무게|weight)'),
    'fasting_glucose':('공복혈당', 'mg/dL', r'(?:공복\s*혈당|fasting)'),
    'post_glucose':   ('식후혈당', 'mg/dL', r'(?:식후\s*혈당|post)'),
    'glucose':        ('혈당', 'mg/dL', r'혈당'),  # '공복/식후' 없이 단독일 때
    'heart_rate':     ('심박수', 'bpm', r'(?:심박수?|heart\s*rate|hr)'),
    'body_fat':       ('체지방', '%', r'(?:체지방|body\s*fat)'),
    'steps':          ('걸음수', '보', r'(?:걸음수?|steps?)'),
}


def parse(text: str) -> dict:
    """자유 형식 텍스트에서 건강 수치를 추출한다."""
    out = {}
    low = text.lower()

    # 혈압: "120/80" 패턴 (혈압 키워드 근처)
    bp = re.search(r'(?:혈압|bp)\D{0,4}(\d{2,3})\s*[/\-]\s*(\d{2,3})', low)
    if bp:
        out['blood_pressure'] = {'sys': int(bp.group(1)), 'dia': int(bp.group(2))}

    # 공복/식후혈당을 혈당보다 먼저 잡아 단독 '혈당'과 충돌 방지
    consumed = []
    for key in ['fasting_glucose', 'post_glucose', 'weight', 'heart_rate', 'body_fat', 'steps', 'glucose']:
        name, unit, kw = METRICS[key]
        # 이미 공복/식후로 잡힌 위치는 단독 혈당에서 제외
        m = re.search(kw + r'\D{0,4}(\d+(?:\.\d+)?)', low)
        if m:
            span = m.span()
            if key == 'glucose' and any(s <= span[0] < e for s, e in consumed):
                continue
            out[key] = float(m.group(1))
            consumed.append(span)
    return out


def log_entry(text: str) -> dict:
    metrics = parse(text)
    if not metrics:
        return {'saved': 0, 'parsed': {}}
    now = datetime.now()
    os.makedirs(DATA_DIR, exist_ok=True)
    count = 0
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        for metric, value in metrics.items():
            rec = {'ts': now.isoformat(timespec='seconds'),
                   'date': now.strftime('%Y-%m-%d'),
                   'metric': metric, 'value': value}
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
            count += 1
    return {'saved': count, 'parsed': metrics, 'ts': now.isoformat(timespec='seconds')}


def _read_all() -> list:
    if not os.path.exists(LOG_PATH):
        return []
    rows = []
    with open(LOG_PATH, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def _fmt_value(metric: str, value) -> str:
    if metric == 'blood_pressure':
        return f"{value['sys']}/{value['dia']}"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def summary() -> str:
    """metric별 최신값 + 7일 전 대비 추세를 한 줄씩."""
    rows = _read_all()
    if not rows:
        return ''
    names = {**{k: v[0] for k, v in METRICS.items()}, 'blood_pressure': '혈압'}
    units = {**{k: v[1] for k, v in METRICS.items()}, 'blood_pressure': ''}
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    by_metric = {}
    for r in rows:
        by_metric.setdefault(r['metric'], []).append(r)

    lines = []
    order = ['weight', 'fasting_glucose', 'post_glucose', 'glucose',
             'blood_pressure', 'heart_rate', 'body_fat', 'steps']
    for metric in order:
        recs = by_metric.get(metric)
        if not recs:
            continue
        recs.sort(key=lambda x: x['ts'])
        latest = recs[-1]
        line = f"{names.get(metric, metric)} {_fmt_value(metric, latest['value'])}{units.get(metric, '')}"
        # 추세: 7일 이전 마지막 값과 비교 (숫자형만)
        if metric != 'blood_pressure':
            prev = [r for r in recs if r['date'] <= week_ago]
            if prev:
                diff = latest['value'] - prev[-1]['value']
                if abs(diff) >= 0.05:
                    arrow = '▲' if diff > 0 else '▼'
                    dv = diff if not float(diff).is_integer() else int(diff)
                    line += f" ({arrow}{abs(dv):g} vs 지난주)"
        lines.append(line)
    return ' · '.join(lines)


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument('--log', type=str, help='기록할 자유형식 텍스트')
    ap.add_argument('--summary', action='store_true', help='최근값+추세 요약')
    ap.add_argument('--dump', action='store_true', help='원시 로그 출력')
    args = ap.parse_args()

    if args.log:
        print(json.dumps(log_entry(args.log), ensure_ascii=False))
    elif args.summary:
        print(summary())
    elif args.dump:
        print(json.dumps(_read_all(), ensure_ascii=False, indent=2))
    else:
        ap.print_help()
