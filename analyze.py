"""
마케팅조사론 4조 — 오프라인 극장 방문 의향 분석
사용법: python analyze.py 고객 의견.csv
"""

import sys, warnings
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.formula.api import ols

warnings.filterwarnings('ignore')

# ── 터미널 색상 코드 ──────────────────────────────────
class C:
    RESET  = '\033[0m'
    BOLD   = '\033[1m'
    DIM    = '\033[2m'
    BLUE   = '\033[94m'
    GREEN  = '\033[92m'
    RED    = '\033[91m'
    YELLOW = '\033[93m'
    CYAN   = '\033[96m'
    WHITE  = '\033[97m'
    GRAY   = '\033[90m'
    BG_BLUE  = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_RED   = '\033[41m'

def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
def blue(s):   return f"{C.BLUE}{s}{C.RESET}"
def green(s):  return f"{C.GREEN}{s}{C.RESET}"
def red(s):    return f"{C.RED}{s}{C.RESET}"
def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
def cyan(s):   return f"{C.CYAN}{s}{C.RESET}"
def gray(s):   return f"{C.GRAY}{s}{C.RESET}"
def dim(s):    return f"{C.DIM}{s}{C.RESET}"

def section(title, subtitle=''):
    print()
    print(f"{C.BG_BLUE}{C.WHITE}{C.BOLD}  {title}  {C.RESET}")
    if subtitle:
        print(gray(f"  {subtitle}"))
    print()

def badge_pass(): return f"{C.BG_GREEN}{C.WHITE} 채택 {C.RESET}"
def badge_fail(): return f"{C.BG_RED}{C.WHITE} 기각 {C.RESET}"
def badge_sig():  return f"{green('● 유의')}"
def badge_ns():   return f"{red('● 비유의')}"

def divider(char='─', width=64):
    print(gray(char * width))

def mini_bar(val, max_val=5.0, width=20, color=C.BLUE):
    filled = int(val / max_val * width)
    bar = '█' * filled + '░' * (width - filled)
    return f"{color}{bar}{C.RESET}"

def pct_bar(pct, width=24):
    filled = int(pct / 100 * width)
    bar = '█' * filled + '░' * (width - filled)
    if pct >= 50:
        color = C.GREEN
    elif pct >= 25:
        color = C.YELLOW
    else:
        color = C.RED
    return f"{color}{bar}{C.RESET} {C.BOLD}{pct:.1f}%{C.RESET}"

# ════════════════════════════════════════════════════════
# 데이터 로드 & 전처리
# ════════════════════════════════════════════════════════
csv_path = sys.argv[1] if len(sys.argv) > 1 else '고객 의견.csv'
print(f"\n{C.BOLD}{C.CYAN}{'='*64}{C.RESET}")
print(f"{C.BOLD}{C.WHITE}  마케팅조사론 4조 — 오프라인 극장 방문 의향 분석{C.RESET}")
print(f"{C.BOLD}{C.CYAN}{'='*64}{C.RESET}")
print(f"  {gray('CSV :')} {csv_path}")

df = pd.read_csv(csv_path)
col_map = {
    '1. 귀하의 성별은 무엇입니까?': 'V1',
    '2. 귀하의 연령대는 어떻게 되십니까?': 'V2',
    '3. 귀하의 거주 지역은 어디입니까?': 'V3',
    '4. 현재 OTT 서비스(넷플릭스, 티빙, 디즈니플러스 등)를 구독하고 있으신가요?': 'V4',
    '5. 최근 3개월 이내 멀티플렉스 극장(CGV·메가박스·롯데시네마)을 방문한 경험이 있습니까?': 'V5',
    '6. 있다면, 최근 3달간 평균 몇 회 방문하셨습니까?': 'V6',
    '7. 극장 방문 시 주로 누구와 함께 가시나요?': 'V7',
    '8. 극장을 가지 않게 되는 주된 이유는 무엇입니까?': 'V8',
    '9. 방문 의향에 영향을 미치는 요인 [현재 멀티플렉스 티켓 가격(10000~15000원)은 적절하다]': 'V9',
    '9. 방문 의향에 영향을 미치는 요인 [할인 혜택(카드·멤버십·통신사 등)이 방문 의향에 영향을 미친다]': 'V10',
    '9. 방문 의향에 영향을 미치는 요인 [팝콘 등 극장 내 식음료 가격이 방문 의향에 영향을 미친다]': 'V11',
    '9. 방문 의향에 영향을 미치는 요인 [집에서 멀티플렉스 극장까지의 거리가 방문 의향에 영향을 미친다]': 'V12',
    '9. 방문 의향에 영향을 미치는 요인 [주변에서 이용 가능한 극장이 줄어든 것을 체감하고 있다]': 'V13',
    '9. 방문 의향에 영향을 미치는 요인 [대형 스크린과 고품질 음향은  방문 의향에 영향을 미친다]': 'V14',
    '9. 방문 의향에 영향을 미치는 요인 [좌석 편안함(리클라이너·단차 등)이 방문 의향에 영향을 미친다]': 'V15',
    '9. 방문 의향에 영향을 미치는 요인 [4DX·ScreenX 등 특수 상영관이 방문 의향을 높인다]': 'V16',
    '9. 방문 의향에 영향을 미치는 요인 [보고 싶은 영화가 있을 때 반드시 극장을 찾게 된다]': 'V17',
    '9. 방문 의향에 영향을 미치는 요인 [OTT보다 먼저 볼 수 있다는 점(개봉 시기 차이)이 방문 의향에 영향을 미친다]': 'V18',
    '9. 방문 의향에 영향을 미치는 요인 [시사회·무대인사·GV(감독·배우 대화) 등의 이벤트가 방문 의향을 높인다]': 'V19',
    '9. 방문 의향에 영향을 미치는 요인 [한정판 굿즈·포토카드 등 특전 제공이 방문 의향에 영향을 미친다]': 'V20',
    "9. 방문 의향에 영향을 미치는 요인 [극장 방문은 단순 영화 시청 외에 '외출·나들이' 로서 의미가 있다]": 'V21',
    '9. 방문 의향에 영향을 미치는 요인 [혼자서도 극장을 방문하는 것에 거부감이 없다]': 'V22',
    '9. 방문 의향에 영향을 미치는 요인 [앞으로 6개월 이내에 멀티플렉스 극장을 방문할 의향이 있다]': 'V27',
    '10. 극장이 개선되어야 할 부분 중 가장 중요하다고 생각하는 것은 무엇입니까?': 'V28',
}
df = df.rename(columns=col_map)
lmap = {'전혀 그렇지 않다': 1, '그렇지 않다': 2, '보통이다': 3, '그렇다': 4, '매우 그렇다': 5}
lcols = ['V9','V10','V11','V12','V13','V14','V15','V16','V17','V18','V19','V20','V21','V22','V27']
for c in lcols:
    df[c] = df[c].map(lmap)
df['V9r'] = 6 - df['V9']
df['F1'] = df[['V9r','V10','V11']].mean(1)
df['F2'] = df[['V12','V13']].mean(1)
df['F3'] = df[['V14','V15','V16']].mean(1)
df['F4'] = df[['V17','V18','V19','V20']].mean(1)
df['F5'] = df[['V21','V22']].mean(1)
df['V5'] = df['V5'].replace({'있다': '있다(다음 질문으로)'})
df['AGE2'] = df['V2'].map({'10대':'20대 이하','20대':'20대 이하','30대':'30대 이상','40대':'30대 이상','50대 이상':'30대 이상'})
df['ING'] = df['V27'].apply(lambda x: '높음(4~5)' if x >= 4 else '낮음(1~3)' if pd.notna(x) else np.nan)
N = len(df)
print(f"  {gray('응답자:')} {bold(str(N))}명  {gray('|')}  전처리 완료\n")

# ════════════════════════════════════════════════════════
# 1. 표본 특성
# ════════════════════════════════════════════════════════
section("1. 표본 특성", "응답자 인구통계학적 분포")

demo_items = [
    ('성별', 'V1'),
    ('연령대', 'V2'),
    ('거주지', 'V3'),
    ('OTT 구독', 'V4'),
]
for label, col in demo_items:
    counts = df[col].value_counts()
    print(f"  {bold(label)}")
    for name, cnt in counts.items():
        pct = cnt / N * 100
        print(f"    {name:<20} {pct_bar(pct)}  {gray(f'({cnt}명)')}")
    print()

# 방문 경험
visit_y = int((df['V5'] == '있다(다음 질문으로)').sum())
visit_n = int((df['V5'] == '없다(7번 문항으로)').sum())
print(f"  {bold('최근 3개월 방문 경험')}")
print(f"    {'있다':<20} {pct_bar(visit_y/N*100)}  {gray(f'({visit_y}명)')}")
print(f"    {'없다':<20} {pct_bar(visit_n/N*100)}  {gray(f'({visit_n}명)')}")
print()

# 방문 횟수
freq = df['V6'].value_counts()
print(f"  {bold('방문 빈도 (방문자 기준, 42명)')}")
for name, cnt in freq.items():
    pct = cnt / visit_y * 100
    print(f"    {name:<20} {pct_bar(pct)}  {gray(f'({cnt}명)')}")
print()

# 방문의향 분포
dist = df['V27'].value_counts().sort_index()
print(f"  {bold('향후 방문 의향 분포 (종속변수 V27)')}")
labels_5 = {1:'1점 전혀 없다', 2:'2점', 3:'3점 보통', 4:'4점', 5:'5점 매우 있다'}
for score, cnt in dist.items():
    pct = cnt / N * 100
    print(f"    {labels_5.get(int(score), str(score)):<20} {pct_bar(pct)}  {gray(f'({int(cnt)}명)')}")

# ════════════════════════════════════════════════════════
# 2. 기술통계
# ════════════════════════════════════════════════════════
section("2. 기술통계", "리커트 문항별 평균 · 표준편차 (5점 척도)")

factor_groups = {
    '비용 요인':      [('V9','티켓 가격 적절성'),('V10','할인 혜택 영향'),('V11','식음료 가격 영향')],
    '접근성 요인':    [('V12','거리·접근성 영향'),('V13','극장 감소 체감')],
    '시설 요인':      [('V14','스크린·음향 차별'),('V15','좌석 편안함'),('V16','특수 상영관')],
    '콘텐츠·이벤트': [('V17','보고 싶은 영화→극장'),('V18','OTT 홀드백'),('V19','이벤트'),('V20','굿즈·특전')],
    '사회·경험 요인': [('V21','외출·나들이 의미'),('V22','혼자 방문 거부감 없음')],
    '종속변수':       [('V27','향후 방문 의향 (V27)')],
}

print(f"  {'요인':<14} {'문항':<22} {'평균':>6}  {'막대그래프':<26} {'std':>5}  {'수준'}")
divider()
for factor, items in factor_groups.items():
    means = [df[c].mean() for c, _ in items]
    factor_mean = np.mean(means)
    print(f"  {cyan(bold(factor))}")
    for col, name in items:
        m = df[col].mean()
        s = df[col].std()
        bar = mini_bar(m, 5.0, 18, C.BLUE)
        lvl = green('긍정') if m >= 4 else (yellow('보통') if m >= 3 else red('부정'))
        print(f"    {'':2}{name:<22} {m:>5.2f}  {bar}  {s:>4.2f}  {lvl}")
    divider('·', 64)

print()
print(f"  {bold('요인별 평균 점수 비교 (5점 만점)')}")
print()
for factor, items in list(factor_groups.items())[:-1]:
    means = [df[c].mean() for c, _ in items]
    fm = np.mean(means)
    bar = mini_bar(fm, 5.0, 24, C.CYAN)
    print(f"  {factor:<14} {bar}  {bold(f'{fm:.2f}')}")

# ════════════════════════════════════════════════════════
# 3. 신뢰도 분석
# ════════════════════════════════════════════════════════
section("3. 신뢰도 분석 — Cronbach α", "α ≥ 0.6 수용 가능 / α ≥ 0.7 권장")

def cronbach(d):
    d = d.dropna(); k = d.shape[1]
    if k < 2: return 0.0
    return round((k/(k-1)) * (1 - d.var(0, ddof=1).sum() / d.sum(1).var(ddof=1)), 3)

alpha_data = {
    '비용 요인':      df[['V9r','V10','V11']],
    '접근성 요인':    df[['V12','V13']],
    '시설 요인':      df[['V14','V15','V16']],
    '콘텐츠·이벤트': df[['V17','V18','V19','V20']],
    '사회·경험 요인': df[['V21','V22']],
}

print(f"  {'요인':<16} {'α 계수':>7}  {'기준선 0.6':^26}  {'판정'}")
divider()
for name, cols in alpha_data.items():
    a = cronbach(cols)
    filled = int(min(a, 1.0) * 24)
    bar_color = C.GREEN if a >= 0.6 else C.RED
    bar = f"{bar_color}{'█' * filled}{'░' * (24-filled)}{C.RESET}"
    threshold_pos = int(0.6 * 24)
    verdict = f"{green('✔ 수용')}" if a >= 0.7 else (f"{yellow('△ 경계')}" if a >= 0.6 else f"{red('✘ 낮음')}")
    print(f"  {name:<16} {bold(f'{a:>5.3f}')}  {bar}  {verdict}")

print()
print(f"  {yellow('⚠')} {dim('비용·접근성·사회경험 α가 낮은 것은 표본 수(51명) 및 문항 수 부족 때문일 수 있음')}")
print(f"    {dim('→ 보고서 한계점에 명시 권장')}")

# ════════════════════════════════════════════════════════
# 4. 상관분석
# ════════════════════════════════════════════════════════
section("4. 상관분석 — 피어슨 상관계수 (r)", "종속변수 V27(향후 방문 의향)과의 상관")

print(f"  {gray('|r| 0.1~0.3 약한 / 0.3~0.5 중간 / 0.5↑ 강한  |  p < 0.05 유의')}")
print()
print(f"  {'요인':<16} {'r':>7}  {'방향과 강도':^28}  {'p값':>7}  {'유의성'}")
divider()

y = df['V27'].dropna()
for name, fc in [('비용 요인','F1'),('접근성 요인','F2'),('시설 요인','F3'),('콘텐츠·이벤트','F4'),('사회·경험 요인','F5')]:
    x = df[fc]; mask = x.notna() & y.notna()
    r, p = stats.pearsonr(x[mask], y[mask])
    abs_r = abs(r)
    filled = int(abs_r / 0.6 * 20)
    col = C.GREEN if p < 0.05 else C.GRAY
    bar = f"{col}{'█' * min(filled,20)}{'░' * max(0, 20-filled)}{C.RESET}"
    sig_str = badge_sig() if p < 0.05 else badge_ns()
    strength = '강한 상관' if abs_r >= 0.5 else ('중간 상관' if abs_r >= 0.3 else '약한 상관')
    r_str = f"{green(bold(f'{r:+.3f}'))}" if p < 0.05 else f"{gray(f'{r:+.3f}')}"
    print(f"  {name:<16} {r_str}  {bar}  {p:>7.3f}  {sig_str}  {dim(strength)}")

# ════════════════════════════════════════════════════════
# 5. 다중회귀분석
# ════════════════════════════════════════════════════════
section("5. 다중회귀분석 — H1 ~ H5 검증", "방문 의향에 미치는 요인별 독립적 영향력")

rd = df[['V27','F1','F2','F3','F4','F5']].dropna()
mod = ols('V27~F1+F2+F3+F4+F5', data=rd).fit()

print(f"  {bold('모형 적합도')}")
r2_bar = mini_bar(mod.rsquared, 1.0, 24, C.BLUE)
print(f"  R²        {r2_bar}  {bold(blue(f'{mod.rsquared:.3f}'))}  ({mod.rsquared*100:.1f}% 설명)")
print(f"  수정 R²   {mini_bar(mod.rsquared_adj, 1.0, 24, C.CYAN)}  {f'{mod.rsquared_adj:.3f}'}")
fp_str = green(f'p = {mod.f_pvalue:.4f} ✔ 유의') if mod.f_pvalue < 0.05 else red(f'p = {mod.f_pvalue:.4f}')
print(f"  F 통계량  {bold(f'{mod.fvalue:.3f}'):>8}  {fp_str}")
print()

hypo_info = {
    'F1': ('H1', '비용 요인',      '비용 부담↓ → 방문 의향↑'),
    'F2': ('H2', '접근성 요인',    '접근성↑ → 방문 의향↑'),
    'F3': ('H3', '시설 요인',      '시설 만족↑ → 방문 의향↑'),
    'F4': ('H4', '콘텐츠·이벤트', '콘텐츠 기대↑ → 방문 의향↑'),
    'F5': ('H5', '사회·경험 요인', '사회적 경험↑ → 방문 의향↑'),
}

print(f"  {'가설':<5} {'요인':<14} {'β계수':>7}  {'영향력':^22}  {'p값':>7}  {'결과'}")
divider()
for fc, (hid, name, desc) in hypo_info.items():
    b = mod.params[fc]
    p = mod.pvalues[fc]
    abs_b = abs(b)
    col = C.GREEN if p < 0.05 else C.GRAY
    filled = int(min(abs_b / 0.5, 1.0) * 20)
    bar = f"{col}{'█' * filled}{'░' * (20-filled)}{C.RESET}"
    verdict = badge_pass() if p < 0.05 else badge_fail()
    b_str = f"{green(bold(f'{b:+.3f}'))}" if p < 0.05 else f"{gray(f'{b:+.3f}')}"
    print(f"  {bold(hid):<5} {name:<14} {b_str}  {bar}  {p:>7.3f}  {verdict}")
    print(f"  {'':5} {dim(desc)}")

# ════════════════════════════════════════════════════════
# 6. 교차분석
# ════════════════════════════════════════════════════════
section("6. 교차분석 — 카이제곱 검정 (H6, H7)", "인구통계 변수에 따른 방문 의향 차이 검증")

cross_cases = [
    ('H6', '연령대 × 방문 의향', df['AGE2'], df['ING']),
    ('H7', 'OTT 구독 × 방문 의향', df['V4'], df['ING']),
]
for hid, title, grp, outcome in cross_cases:
    ct = pd.crosstab(grp, outcome)
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    verdict = badge_pass() if p < 0.05 else badge_fail()
    sig_str = green('유의한 차이 있음') if p < 0.05 else red('유의한 차이 없음')
    print(f"  {bold(hid)} — {bold(title)}")
    print(f"  χ² = {bold(f'{chi2:.3f}')}  |  df = {dof}  |  p = {bold(f'{p:.3f}')}  →  {verdict}  {sig_str}")
    print()

    # 교차표 출력
    col_w = 12
    header = f"  {'':16}" + ''.join(f"{str(c):^{col_w}}" for c in ct.columns) + f"{'합계':^{col_w}}"
    print(gray(header))
    divider('·', 64)
    for row in ct.index:
        row_total = ct.loc[row].sum()
        row_str = f"  {bold(str(row)):<16}"
        for col_name in ct.columns:
            val = ct.loc[row, col_name]
            pct = val / row_total * 100
            col = C.GREEN if col_name == '높음(4~5)' else C.RED
            row_str += f"{col}{val:>5}명({pct:.0f}%){C.RESET}  "
        row_str += f"{gray(f'  {row_total}명')}"
        print(row_str)
    divider('·', 64)
    print()

# ════════════════════════════════════════════════════════
# 7. 복수응답 빈도분석
# ════════════════════════════════════════════════════════
section("7. 복수응답 빈도분석 — H8", "극장을 가지 않는 이유 · 개선 우선순위")

reason_labels = [
    '상영중인 영화 중 보고 싶은 영화가 없어서',
    '티켓 가격이 부담스러워서',
    '집에서 OTT로 편리하게 볼 수 있어서',
    '극장까지 이동이 번거로워서',
    '함께 갈 사람이 없어서',
    '주변에 극장이 없거나 줄어들어서',
]
rc = {r: 0 for r in reason_labels}
for v in df['V8'].dropna():
    for r in reason_labels:
        if r in str(v): rc[r] += 1

print(f"  {bold('극장을 가지 않게 되는 이유')}  {gray('(복수선택, 응답자 대비 %)')}")
print()
for i, (r, cnt) in enumerate(sorted(rc.items(), key=lambda x: -x[1])):
    pct = cnt / N * 100
    rank = f"  {bold(cyan(str(i+1)+'위'))}" if i == 0 else f"  {gray(str(i+1)+'위')}"
    short = r[:22] + '…' if len(r) > 22 else r
    print(f"{rank}  {short:<26} {pct_bar(pct)}  {gray(f'({cnt}명)')}")

print()
price_cnt = rc['티켓 가격이 부담스러워서']
ott_cnt = rc['집에서 OTT로 편리하게 볼 수 있어서']
content_cnt = rc['상영중인 영화 중 보고 싶은 영화가 없어서']
print(f"  {yellow('⚠')} {bold('H8 검토:')} 콘텐츠 부재({content_cnt}명) > 가격({price_cnt}명) = OTT편의성({ott_cnt}명)")
print(f"    {red('→ H8 기각')} — 예상과 달리 {bold('콘텐츠 부재')}가 1위, 마케팅 전략 방향 수정 필요")
print()

improve_labels = [
    '티켓 가격 인하 또는 할인 혜택 강화',
    '독점·선공개 콘텐츠 확대',
    '이벤트·특별 상영 프로그램 강화',
    '접근성 개선 (더 많은 극장 운영, 교통 편의)',
    '시설 고급화 (좌석·음향·스크린 등)',
    '식음료 가격 합리화',
]
ic = {r: 0 for r in improve_labels}
for v in df['V28'].dropna():
    for r in improve_labels:
        if r in str(v): ic[r] += 1

print(f"  {bold('극장 개선 우선순위')}")
print()
for i, (r, cnt) in enumerate(sorted(ic.items(), key=lambda x: -x[1])):
    pct = cnt / N * 100
    rank = f"  {bold(cyan(str(i+1)+'위'))}" if i == 0 else f"  {gray(str(i+1)+'위')}"
    short = r[:22] + '…' if len(r) > 22 else r
    print(f"{rank}  {short:<26} {pct_bar(pct)}  {gray(f'({cnt}명)')}")

# ════════════════════════════════════════════════════════
# 8. 가설 검정 종합 요약
# ════════════════════════════════════════════════════════
section("8. 가설 검정 종합 요약")

all_hypo = [
    ('H1', '비용 요인 → 방문 의향',       '다중회귀', 0.371, False,  None),
    ('H2', '접근성 요인 → 방문 의향',      '다중회귀', 0.500, False,  None),
    ('H3', '시설 요인 → 방문 의향',        '다중회귀', 0.086, False,  'p=0.086 경계선'),
    ('H4', '콘텐츠·이벤트 → 방문 의향',   '다중회귀', 0.033, True,   None),
    ('H5', '사회·경험 요인 → 방문 의향',   '다중회귀', 0.046, True,   None),
    ('H6', '연령대 → 방문 의향 차이',      '교차분석', 0.047, True,   None),
    ('H7', 'OTT 구독 → 방문 의향 차이',   '교차분석', 0.283, False,  None),
    ('H8', 'OTT편의성 = 미방문 1위',       '복수응답', None,  False,  '실제 1위: 콘텐츠 부재'),
]

divider()
print(f"  {'가설':<5} {'내용':<26} {'방법':<10} {'p값':>7}  {'결과'}")
divider()
for hid, content, method, p, sig, note in all_hypo:
    verdict = badge_pass() if sig else badge_fail()
    p_str = f"{p:>7.3f}" if p is not None else f"{'—':>7}"
    note_str = f"  {dim(note)}" if note else ''
    print(f"  {bold(hid):<5} {content:<26} {gray(method):<10} {p_str}  {verdict}{note_str}")
divider()

accepted = [h for h,_,_,_,s,_ in all_hypo if s]
rejected = [h for h,_,_,_,s,_ in all_hypo if not s]
print(f"\n  채택: {green(bold(', '.join(accepted)))}  ({len(accepted)}개)")
print(f"  기각: {red(', '.join(rejected))}  ({len(rejected)}개)")

# ════════════════════════════════════════════════════════
# 핵심 인사이트
# ════════════════════════════════════════════════════════
print()
print(f"{C.BOLD}{C.CYAN}{'='*64}{C.RESET}")
print(f"{C.BOLD}{C.WHITE}  핵심 인사이트{C.RESET}")
print(f"{C.BOLD}{C.CYAN}{'='*64}{C.RESET}\n")

insights = [
    ("🎬 콘텐츠가 핵심이다",
     "방문 의향에 가장 큰 영향: 콘텐츠·이벤트 (β=0.399)",
     "안 가는 이유 1위도 '콘텐츠 부재' (58.8%)",
     "→ 마케팅 핵심은 가격 경쟁이 아닌 콘텐츠 차별화"),
    ("👥 극장은 '경험'이다",
     "사회·경험 요인 β=0.315 유의 (p=0.046)",
     "외출·나들이 의미 평균 3.51점 — 전체 문항 중 최고",
     "→ 극장을 사회적 경험으로 포지셔닝"),
    ("📺 OTT는 경쟁자가 아니다",
     "OTT 구독 여부와 방문 의향 차이 없음 (p=0.283)",
     "OTT 구독자도 극장을 찾음",
     "→ 극장과 OTT는 대체재가 아닌 보완재"),
]
for title, *lines in insights:
    print(f"  {bold(title)}")
    for line in lines:
        prefix = green('  →') if line.startswith('→') else gray('   •')
        print(f"{prefix} {line.lstrip('→').strip()}")
    print()

print(f"{C.BOLD}{C.CYAN}{'='*64}{C.RESET}\n")