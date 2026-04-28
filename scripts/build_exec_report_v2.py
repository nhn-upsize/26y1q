# -*- coding: utf-8 -*-
"""임원 보고용 리포트 v2 — 근거에 표/차트 시각화 통합"""
import os

OUT = r"C:\Users\NHN\Documents\sensortower_api\reports\NHN_exec_report.html"

# ============================================================
# 차트 빌더 헬퍼
# ============================================================
def bar_compare(rows, title='', unit='억', max_val=None, accent=None):
    """
    rows: [(label, value, color, sub_label), ...]
    다이버징 수평 막대 (0축 기준 양수 오른쪽 / 음수 왼쪽)
    음수가 있으면 자동으로 다이버징 레이아웃, 없으면 일반 좌측 정렬
    """
    if not rows: return ''
    has_negative = any(r[1] < 0 for r in rows)
    has_positive = any(r[1] > 0 for r in rows)
    max_v = max_val or max(abs(r[1]) for r in rows) * 1.25
    n = len(rows)
    row_h = 38
    title_h = 30 if title else 0
    tick_h = 20 if (has_positive and has_negative) else 10
    pad_top = title_h + tick_h
    pad_bot = 14
    total_w = 680
    label_w = 140
    value_w = 90
    bar_area_total = total_w - label_w - value_w
    svg_h = pad_top + n * row_h + pad_bot

    # 축 위치
    if has_negative and has_positive:
        max_neg = max((abs(r[1]) for r in rows if r[1] < 0), default=0)
        max_pos = max((r[1] for r in rows if r[1] > 0), default=0)
        ratio = max_neg / (max_neg + max_pos) if (max_neg + max_pos) else 0.3
        axis_x = label_w + bar_area_total * ratio
    elif has_negative:
        # 전부 음수 — 축을 오른쪽에
        axis_x = label_w + bar_area_total
    else:
        # 전부 양수 — 축을 왼쪽에
        axis_x = label_w

    svg = [f'<svg viewBox="0 0 {total_w} {svg_h}" style="width:100%;max-width:780px;height:auto;display:block;margin:8px 0;">']
    if title:
        svg.append(f'<text x="{total_w/2}" y="18" text-anchor="middle" font-size="12" fill="#334155" font-weight="700">{title}</text>')

    tick_y = pad_top - 6
    # 0 축 (세로선)
    svg.append(f'<line x1="{axis_x}" y1="{pad_top-2}" x2="{axis_x}" y2="{svg_h-pad_bot+2}" stroke="#cbd5e1" stroke-width="1.5"/>')
    # 0 라벨 — 양쪽 다 있을 때만 의미있음
    if has_positive and has_negative:
        svg.append(f'<text x="{axis_x}" y="{tick_y}" text-anchor="middle" font-size="9" fill="#94a3b8">0</text>')

    # 양수쪽 눈금
    if has_positive:
        pos_px = (total_w - value_w) - axis_x
        if pos_px > 20:
            for frac in [0.5, 1.0]:
                gx = axis_x + pos_px * frac
                gv = max_v * frac
                svg.append(f'<line x1="{gx}" y1="{pad_top-2}" x2="{gx}" y2="{svg_h-pad_bot+2}" stroke="#f1f5f9" stroke-dasharray="2,3"/>')
                if frac == 1.0:
                    svg.append(f'<text x="{gx}" y="{tick_y}" text-anchor="middle" font-size="9" fill="#cbd5e1">+{int(gv)}</text>')
    # 음수쪽 눈금
    if has_negative:
        neg_px = axis_x - label_w
        if neg_px > 20:
            for frac in [0.5, 1.0]:
                gx = axis_x - neg_px * frac
                gv = max_v * frac
                svg.append(f'<line x1="{gx}" y1="{pad_top-2}" x2="{gx}" y2="{svg_h-pad_bot+2}" stroke="#f1f5f9" stroke-dasharray="2,3"/>')
                if frac == 1.0:
                    svg.append(f'<text x="{gx}" y="{tick_y}" text-anchor="middle" font-size="9" fill="#cbd5e1">-{int(gv)}</text>')

    for i, row in enumerate(rows):
        label = row[0]; val = row[1]
        color = row[2] if len(row) > 2 else ('#059669' if val >= 0 else '#dc2626')
        sub = row[3] if len(row) > 3 else ''
        y = pad_top + i * row_h + 12
        bar_h = 22

        # label (좌측 이름)
        lbl_color = color if val != 0 else '#64748b'
        svg.append(f'<text x="{label_w - 10}" y="{y+bar_h/2+4}" text-anchor="end" font-size="12" fill="#1e293b" font-weight="700">{label}</text>')

        # bar
        if val >= 0:
            w = val / max_v * pos_px
            bar_x = axis_x
            val_x = bar_x + w + 8
            val_anchor = 'start'
        else:
            w = abs(val) / max_v * (axis_x - label_w)
            bar_x = axis_x - w
            val_x = bar_x - 8
            val_anchor = 'end'

        # 그라데이션 효과
        svg.append(f'<rect x="{bar_x}" y="{y}" width="{w:.1f}" height="{bar_h}" fill="{color}" rx="3" opacity="0.9"/>')

        # 값 라벨
        val_txt = f'+{val:,.0f}{unit}' if val > 0 else f'{val:,.0f}{unit}'
        svg.append(f'<text x="{val_x}" y="{y+bar_h/2+5}" text-anchor="{val_anchor}" font-size="12" fill="{color}" font-weight="800">{val_txt}</text>')

        # sub 라벨 (아래쪽)
        if sub:
            sub_color = '#94a3b8'
            if '+' in sub or '%' in sub and val > 0: sub_color = '#059669'
            elif '-' in sub or '⚠' in sub: sub_color = '#dc2626'
            svg.append(f'<text x="{val_x}" y="{y+bar_h/2+19}" text-anchor="{val_anchor}" font-size="10" fill="{sub_color}" font-weight="600">{sub}</text>')

    svg.append('</svg>')
    return ''.join(svg)

def before_after_bars(rows, title='', unit='억'):
    """
    rows: [(label, before, after, color), ...]
    전/후 duo 바
    """
    if not rows: return ''
    max_v = max(max(r[1], r[2]) for r in rows) * 1.15
    n = len(rows)
    row_h = 44
    title_h = 24 if title else 0
    legend_h = 18
    pad_top = title_h + legend_h + 8
    pad_bot = 14
    total_w = 620; label_w = 160
    bar_area = total_w - label_w - 110
    svg_h = pad_top + n * row_h + pad_bot

    svg = [f'<svg viewBox="0 0 {total_w} {svg_h}" style="width:100%;max-width:740px;height:auto;display:block;margin:8px 0;">']
    if title:
        svg.append(f'<text x="{total_w/2}" y="18" text-anchor="middle" font-size="12" fill="#334155" font-weight="700">{title}</text>')
    # 범례 (제목 아래 별도 줄)
    legend_y = title_h + 10
    svg.append(f'<rect x="{label_w}" y="{legend_y-7}" width="10" height="8" fill="#cbd5e1"/>')
    svg.append(f'<text x="{label_w+14}" y="{legend_y}" font-size="10" fill="#64748b">전 (22~24)</text>')
    svg.append(f'<rect x="{label_w+90}" y="{legend_y-7}" width="10" height="8" fill="#3b82f6"/>')
    svg.append(f'<text x="{label_w+104}" y="{legend_y}" font-size="10" fill="#64748b">후 (25~26.1Q)</text>')

    for i, (label, b, a, color) in enumerate(rows):
        y = pad_top + i * row_h
        b_w = b / max_v * bar_area
        a_w = a / max_v * bar_area
        svg.append(f'<text x="{label_w - 8}" y="{y+14}" text-anchor="end" font-size="11" fill="#1e293b" font-weight="600">{label}</text>')
        # 전
        svg.append(f'<rect x="{label_w}" y="{y}" width="{b_w:.1f}" height="12" fill="#cbd5e1" rx="1"/>')
        svg.append(f'<text x="{label_w + b_w + 4}" y="{y+10}" font-size="10" fill="#64748b">{b:,.0f}{unit}</text>')
        # 후
        svg.append(f'<rect x="{label_w}" y="{y+14}" width="{a_w:.1f}" height="12" fill="{color}" rx="1"/>')
        svg.append(f'<text x="{label_w + a_w + 4}" y="{y+24}" font-size="10" fill="{color}" font-weight="700">{a:,.0f}{unit}</text>')
        # delta
        diff = a - b
        pct = (diff/b*100) if b else 0
        dcolor = '#059669' if diff > 0 else '#dc2626'
        svg.append(f'<text x="{total_w - 8}" y="{y+17}" text-anchor="end" font-size="10" fill="{dcolor}" font-weight="700">{diff:+,.0f} ({pct:+.0f}%)</text>')
    svg.append('</svg>')
    return ''.join(svg)

def line_chart(series_data, x_labels, title='', y_max=None, unit='%'):
    """
    series_data: [{'name':'KR','color':'#3b82f6','values':[...]}]
    x_labels: ['2022','2023',...]
    """
    W = 600; H = 240
    left, right, top, bot = 60, 500, 50, 195
    all_vals = [v for s in series_data for v in s['values']]
    ymax = y_max or max(all_vals) * 1.2
    xs = [left + i*((right-left)/(len(x_labels)-1)) for i in range(len(x_labels))]

    svg = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:720px;height:auto;display:block;margin:8px 0;">']
    if title:
        svg.append(f'<text x="{W/2}" y="22" text-anchor="middle" font-size="12" fill="#334155" font-weight="700">{title}</text>')

    # grid
    for gi in range(5):
        gv = ymax * gi / 4
        y = bot - (bot-top) * gi / 4
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#f1f5f9" stroke-dasharray="2,2"/>')
        svg.append(f'<text x="{left-5}" y="{y+3:.1f}" text-anchor="end" font-size="9" fill="#94a3b8">{gv:.0f}{unit}</text>')
    for i, lbl in enumerate(x_labels):
        svg.append(f'<text x="{xs[i]:.1f}" y="{bot+16}" text-anchor="middle" font-size="10" fill="#64748b" font-weight="600">{lbl}</text>')

    # lines
    for s in series_data:
        color = s['color']
        vals = s['values']
        pts = [(xs[i], bot - (bot-top) * vals[i] / ymax) for i in range(len(vals))]
        pts_str = ' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
        svg.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{pts_str}"/>')
        for i, (x, y) in enumerate(pts):
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>')
        # 끝 값 라벨
        svg.append(f'<text x="{pts[-1][0]+6:.1f}" y="{pts[-1][1]+3:.1f}" font-size="10" fill="{color}" font-weight="700">{s["name"]}: {vals[-1]:.1f}{unit}</text>')

    svg.append('</svg>')
    return ''.join(svg)

def line_chart_multi(series_data, x_labels, title='', y_max=None, unit='억', y_step=None):
    """다중 라인 차트 — 각 시리즈 끝에 라벨 표시"""
    W = 720; H = 280
    left, right, top, bot = 60, 590, 55, 225
    all_vals = [v for s in series_data for v in s['values']]
    ymax = y_max or (max(all_vals) * 1.15)
    xs = [left + i*((right-left)/(len(x_labels)-1)) for i in range(len(x_labels))]
    step = y_step or (ymax // 4)

    svg = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:820px;height:auto;display:block;margin:8px 0;">']
    if title:
        svg.append(f'<text x="{(left+right)/2}" y="22" text-anchor="middle" font-size="12" fill="#334155" font-weight="700">{title}</text>')

    # grid
    for v in range(0, int(ymax)+1, int(step)):
        y = bot - (bot-top) * v / ymax
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#f1f5f9" stroke-dasharray="2,2"/>')
        svg.append(f'<text x="{left-4}" y="{y+3:.1f}" text-anchor="end" font-size="9" fill="#94a3b8">{v:,}{unit}</text>')
    for i, lbl in enumerate(x_labels):
        c = '#f59e0b' if '26' in lbl else '#64748b'
        w = '800' if '26' in lbl else '600'
        svg.append(f'<text x="{xs[i]:.1f}" y="{bot+18}" text-anchor="middle" font-size="10" fill="{c}" font-weight="{w}">{lbl}</text>')

    # 라인 + 마지막 값 라벨은 오른쪽 영역에
    label_offsets = []  # 라벨 겹침 방지
    for s in sorted(series_data, key=lambda x: -x['values'][-1]):
        color = s['color']
        vals = s['values']
        pts = [(xs[i], bot - (bot-top) * vals[i] / ymax) for i in range(len(vals))]
        pts_str = ' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
        svg.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{pts_str}"/>')
        for i, (x, y) in enumerate(pts):
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>')

        # 끝점 라벨 (오른쪽)
        end_x = pts[-1][0]
        end_y = pts[-1][1]
        # 겹침 조정
        adjusted_y = end_y
        for ey in label_offsets:
            if abs(adjusted_y - ey) < 14:
                adjusted_y = ey + 14
        label_offsets.append(adjusted_y)
        svg.append(f'<text x="{end_x+8}" y="{adjusted_y+4}" font-size="11" fill="{color}" font-weight="800">{s["name"]} {vals[-1]:,.0f}</text>')

    svg.append('</svg>')
    return ''.join(svg)

def stacked_bar_yearly(series_data, x_labels, title='', unit='억', decimals=0, y_step=None):
    """누적 바 (연도별 구성)
    decimals: 값 표시 소수점 자리수 (0=정수, 1=0.1 자리)
    y_step: y축 grid 간격 (None=자동)
    """
    W = 720; H = 340
    title_h = 24 if title else 0
    legend_lines = len(series_data)
    legend_h = legend_lines * 16 + 10
    left = 60
    right = 660
    top = title_h + legend_h + 20
    bot = H - 50  # X labels 영역 확보
    # 각 x 위치의 총합 구해 max 결정
    totals = []
    for i in range(len(x_labels)):
        t = sum(s['values'][i] for s in series_data)
        totals.append(t)
    ymax_raw = max(totals) * 1.12
    xs = [left + i*((right-left)/(len(x_labels)-1)) for i in range(len(x_labels))]
    bar_w = 50

    # y_step 자동 추정
    if y_step is None:
        if ymax_raw <= 12:
            y_step = 1
        elif ymax_raw <= 60:
            y_step = 10
        elif ymax_raw <= 200:
            y_step = 50
        elif ymax_raw <= 600:
            y_step = 100
        else:
            y_step = 500
    ymax = ymax_raw

    svg = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:820px;height:auto;display:block;margin:8px 0;">']
    if title:
        svg.append(f'<text x="{(left+right)/2}" y="18" text-anchor="middle" font-size="12" fill="#334155" font-weight="700">{title}</text>')

    # 범례 (제목 아래 별도 블록, 좌측부터 수평 or 수직)
    ly_start = title_h + 14
    for si, s in enumerate(series_data):
        lx_box = left
        lx_txt = left + 14
        ly = ly_start + si * 16
        svg.append(f'<rect x="{lx_box}" y="{ly-8}" width="10" height="10" fill="{s["color"]}" rx="1"/>')
        svg.append(f'<text x="{lx_txt}" y="{ly}" font-size="10" fill="#475569">{s["name"]}</text>')

    # grid
    v = 0
    while v <= ymax:
        y = bot - (bot-top) * v / ymax
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#f1f5f9" stroke-dasharray="2,2"/>')
        label_v = f'{v:.0f}' if decimals == 0 else f'{v:.{decimals}f}'
        svg.append(f'<text x="{left-4}" y="{y+3:.1f}" text-anchor="end" font-size="9" fill="#94a3b8">{label_v}{unit}</text>')
        v += y_step

    # 막대 누적
    for i, lbl in enumerate(x_labels):
        cx = xs[i]
        cum = 0
        for s in series_data:
            val = s['values'][i]
            h = (bot-top) * val / ymax
            y0 = bot - (bot-top) * cum / ymax - h
            svg.append(f'<rect x="{cx - bar_w/2}" y="{y0:.1f}" width="{bar_w}" height="{h:.1f}" fill="{s["color"]}" opacity="0.88"/>')
            if h > 16:
                svg.append(f'<text x="{cx}" y="{y0 + h/2 + 4:.1f}" text-anchor="middle" font-size="10" fill="#fff" font-weight="700">{val:,.{decimals}f}</text>')
            cum += val
        # 총합 라벨 (막대 위)
        top_y = bot - (bot-top) * cum / ymax
        svg.append(f'<text x="{cx}" y="{top_y - 6:.1f}" text-anchor="middle" font-size="11" fill="#1e293b" font-weight="800">{cum:,.{decimals}f}</text>')
        # X 라벨 (하단 여유)
        c = '#f59e0b' if '26' in lbl else '#64748b'
        w = '800' if '26' in lbl else '600'
        svg.append(f'<text x="{cx}" y="{bot+18}" text-anchor="middle" font-size="10" fill="{c}" font-weight="{w}">{lbl}</text>')

    svg.append('</svg>')
    return ''.join(svg)

def rank_line_chart(rank_data, x_labels, country_color='#ef4444', title=''):
    """순위별 매출 추이 라인 차트 (로그 스케일)
    rank_data: {'1위':[...], '10위':[...], ...}
    """
    import math
    W = 720; H = 300
    left, right, top, bot = 70, 620, 55, 245
    all_vals = [v for rs in rank_data.values() for v in rs]
    log_min = math.floor(math.log10(max(min(all_vals), 1)))
    log_max = math.ceil(math.log10(max(all_vals)))
    def yc(v):
        if v <= 0: return bot
        lv = math.log10(v)
        return top + (bot-top) * (1 - (lv - log_min) / (log_max - log_min))
    xs = [left + i*((right-left)/(len(x_labels)-1)) for i in range(len(x_labels))]

    # 순위별 색상 (진한 → 연한)
    rank_colors_map = {
        '#ef4444': ['#991b1b','#dc2626','#ef4444','#f87171','#fca5a5'],
        '#3b82f6': ['#1e40af','#2563eb','#3b82f6','#60a5fa','#93c5fd'],
        '#a855f7': ['#581c87','#7c3aed','#a855f7','#c084fc','#d8b4fe'],
    }
    palette = rank_colors_map.get(country_color, rank_colors_map['#ef4444'])

    svg = [f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:820px;height:auto;display:block;margin:8px 0;">']
    if title:
        svg.append(f'<text x="{(left+right)/2}" y="22" text-anchor="middle" font-size="12" fill="#334155" font-weight="700">{title}</text>')

    # Y grid
    for exp in range(int(log_min), int(log_max)+1):
        v = 10**exp
        y = yc(v)
        svg.append(f'<line x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}" stroke="#f1f5f9" stroke-dasharray="2,2"/>')
        label = f'{v:,}억' if v < 10000 else f'{v//10000:,}만억'
        svg.append(f'<text x="{left-6}" y="{y+3:.1f}" text-anchor="end" font-size="9" fill="#94a3b8">{label}</text>')

    # X labels
    for i, lbl in enumerate(x_labels):
        c = '#f59e0b' if '26' in lbl else '#64748b'
        w = '800' if '26' in lbl else '600'
        svg.append(f'<text x="{xs[i]:.1f}" y="{bot+18}" text-anchor="middle" font-size="10" fill="{c}" font-weight="{w}">{lbl}</text>')

    # 라인
    for ri, rank in enumerate(['1위','10위','20위','50위','100위']):
        rc = palette[ri]
        vals = rank_data[rank]
        pts = [(xs[i], yc(vals[i])) for i in range(len(vals))]
        pts_str = ' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
        svg.append(f'<polyline fill="none" stroke="{rc}" stroke-width="2.5" points="{pts_str}"/>')
        for i, (x, y) in enumerate(pts):
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{rc}"/>')
        # 끝 라벨
        svg.append(f'<text x="{pts[-1][0]+8:.1f}" y="{pts[-1][1]+4:.1f}" font-size="11" fill="{rc}" font-weight="800">{rank} ({vals[-1]}억)</text>')

    svg.append('</svg>')
    return ''.join(svg)

def mini_table(headers, rows, accent='#0085ca'):
    """간단한 표"""
    html = '<table class="mini-table"><thead><tr>'
    for h in headers: html += f'<th>{h}</th>'
    html += '</tr></thead><tbody>'
    for row in rows:
        html += '<tr>'
        for i, cell in enumerate(row):
            cls = ' class="num"' if i > 0 else ''
            html += f'<td{cls}>{cell}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

# ============================================================
# 인사이트 (차트 포함)
# ============================================================
INSIGHTS = [
    {
        'id': 'kr-1',
        'section': 'KR',
        'headline': '한국 시장 +13% 성장 중 — 성장 주체 재편',
        'interpretation': '표면적으로 KR 퍼블 -6%만 보면 한국 시장 축소로 해석될 수 있으나, 실제 <strong>전체 시장은 4,109억 → 4,654억으로 +545억(+13%) 성장</strong>. KR 퍼블 감소분(-146억)보다 중화권 증가분(+568억)이 <strong>4배</strong> 큰 규모로 시장 성장을 단독 견인하는 구조. 매출 기준 변화는 상대적으로 완만하지만, 성장 주체가 바뀐 크기는 점유율 관점에서 보다 선명하게 드러남.',
        'chart': line_chart_multi([
            {'name':'전체 시장',   'color':'#1e40af', 'values':[3835, 4003, 4488, 4800, 4071]},
            {'name':'KR 퍼블',    'color':'#dc2626', 'values':[2565, 2548, 2276, 2405, 1964]},
            {'name':'중화권',     'color':'#f59e0b', 'values':[ 849, 1030, 1619, 1775, 1555]},
            {'name':'북미·기타',   'color':'#64748b', 'values':[ 421,  425,  593,  620,  552]},
        ], ['2022','2023','2024','2025','26.1Q'],
           title='KR 시장 구성 주체별 월평균 매출 추이 (억/월)',
           y_max=5200, y_step=1000, unit='억')
        + before_after_bars([
            ('전체 시장',  4109, 4654, '#1e40af'),
            ('KR 퍼블',   2463, 2317, '#dc2626'),
            ('중화권',    1154, 1722, '#f59e0b'),
            ('북미·기타',  492,  615, '#64748b'),
        ], title='25년 전후 월평균 매출 비교 (22~24 vs 25~26.1Q, 억)', unit='억'),
        'evidence': [
            ('전체 시장', '4,109억 → 4,654억 (+545억, +13%)'),
            ('KR 퍼블', '2,463억 → 2,317억 (-146억, -6%)'),
            ('중화권', '1,154억 → 1,722억 (+568억, +49%)'),
            ('요점', 'KR 퍼블 감소(-146)의 <strong>4배</strong>를 중화권(+568)이 차지'),
        ],
    },
    {
        'id': 'kr-4',
        'section': 'KR',
        'headline': 'KR 퍼블 점유율 67% → 48%로 19%p 하락',
        'interpretation': '성장 주체 재편을 점유율 관점에서 확인. 매출 기준으로는 KR 퍼블 -6% 감소에 그치지만, 시장 성장분(+13%)이 중화권에 집중되면서 <strong>점유율 기준으로는 KR 퍼블 66.9% → 48.2% (-18.7%p)</strong>. 동기간 <strong>중화권은 21.8% → 37.7% (+15.9%p)</strong>로 상승. 격차가 45%p → 10.5%p로 좁혀졌으며, 현 추세 지속 시 <strong>26~27년 중 중화권이 KR 퍼블 점유율을 추월할 가능성</strong>.',
        'chart': line_chart([
            {'name':'KR 퍼블', 'color':'#3b82f6', 'values':[66.9, 63.7, 50.7, 50.1, 48.2]},
            {'name':'중화권', 'color':'#f59e0b', 'values':[21.8, 25.5, 35.8, 36.9, 37.7]},
        ], ['22', '23', '24', '25', '26.1Q'], title='KR 시장 점유율 추이 (%)', y_max=80, unit='%'),
        'evidence': [
            ('KR 퍼블', "66.9% → 48.2% (-18.7%p)"),
            ('중화권', "21.8% → 37.7% (+15.9%p)"),
            ('격차', '45%p → 10.5%p로 34.5%p 축소'),
            ('요점', '매출 감소폭(-6%) 대비 점유율 하락폭(-19%p)이 크게 나타나는 구조'),
        ],
    },
    {
        'id': 'kr-2b',
        'section': 'KR',
        'headline': 'KR 퍼블 매출 감소의 실제 주체는 TOP5 외 중소 퍼블',
        'interpretation': '점유율이 하락한 KR 퍼블 내부를 세분화하면, <strong>TOP5 합계는 1,256 → 1,240억으로 -1% 거의 정체</strong>. 실질 감소 주체는 <strong>TOP5 외 KR 중소 퍼블 — 1,308 → 724억으로 -45% 축소</strong>.<br><br>동시에 <strong>해외 퍼블(중화권·북미·기타)은 1,271 → 2,107억으로 +66% 증가</strong>. 즉 KR 시장의 재편 구조는 <strong>중소 KR 퍼블 감소분이 해외 퍼블에게 흡수되는 형태</strong>이며, TOP5는 상대적으로 포지션을 유지.',
        'chart': stacked_bar_yearly([
            {'name':'TOP5 (엔씨+넥슨+넷마블+카카오+NHN)', 'color':'#3b82f6', 'values':[1256, 1286, 1028, 1333, 1240]},
            {'name':'기타 KR 퍼블',                    'color':'#94a3b8', 'values':[1308, 1262, 1248, 1072,  724]},
            {'name':'해외 퍼블 (중화권/북미/기타)',          'color':'#f59e0b', 'values':[1271, 1455, 2212, 2395, 2107]},
        ], ['2022', '2023', '2024', '2025', '26.1Q'], title='KR 시장 구성 변화 — 연도별 월평균 매출 (억)'),
        'evidence': [
            ('TOP5 변화', "1,256억 ('22) → 1,240억 ('26.1Q) · -1% 거의 정체"),
            ('기타 KR 변화', "1,308억 → 724억 · -45% 거의 반토막"),
            ('해외 퍼블 변화', "1,271억 → 2,107억 · +66% 급증"),
            ('구조적 해석', '시장 규모는 커졌지만 <strong>중소 KR 퍼블이 줄어든 자리를 해외 퍼블이 차지</strong>하는 구도'),
            ('요점', 'KR 퍼블 감소는 <strong>중소 퍼블 영역에 집중</strong>. TOP5는 상대적으로 방어 성공'),
        ],
    },
    {
        'id': 'kr-2',
        'section': 'KR',
        'headline': 'KR TOP5 퍼블리셔 내부에서도 매출 양극화 진행',
        'interpretation': '상대적으로 방어 중인 TOP5 내부를 확인하면, 전체 합계는 정체지만 개별 퍼블 간 매출 궤적은 분기. <strong>엔씨소프트 -280억/월 (-34%)</strong>이 절대 감소액 기준 단일 최대 변동이며, <strong>카카오게임즈 -213억/월 (-57%)</strong>은 감소율 기준 최대. 반면 <strong>넷마블 +191억 (+88%) · 넥슨 +135억 (+34%) · NHN +23억 (+21%)</strong>의 성장이 공존.<br><br>연도별 흐름: <strong>엔씨 리니지 시리즈 전반 하락 (979 → 314억/월)</strong>, <strong>카카오 오딘 발할라 지속 하락 및 후속작 부재 (366 → 93)</strong>, <strong>넥슨 MapleStory Idle 단일 견인으로 26.1Q 759억 급등</strong>. TOP5 합계가 정체로 나타나는 이유는 엔씨·카카오 감소분(-493억)을 넥슨·넷마블·NHN 성장분(+349억)이 부분 상쇄하는 구조.',
        'chart': line_chart_multi([
            {'name':'엔씨',   'color':'#f59e0b', 'values':[979, 767, 734, 603, 314]},
            {'name':'넥슨',   'color':'#059669', 'values':[484, 453, 257, 476, 759]},
            {'name':'카카오',  'color':'#dc2626', 'values':[366, 431, 332, 180,  93]},
            {'name':'넷마블',  'color':'#10b981', 'values':[220, 203, 224, 466, 174]},
            {'name':'NHN',    'color':'#0085ca', 'values':[ 86, 112, 125, 129, 136]},
        ], ['2022', '2023', '2024', '2025', '26.1Q'], title='KR TOP5 퍼블리셔 연도별 월평균 매출 (억)', y_max=1200, y_step=300, unit=''),
        'evidence': [
            ('엔씨소프트', "'22 979억 → '26.1Q 314억 (-68%) · 전후 826→546 (<strong>-280억, -34%</strong>) · 리니지 시리즈 전반 하락, AION2 신규 진입"),
            ('카카오게임즈', "'22 366억 → '26.1Q 93억 (-75%) · 전후 376→163 (<strong>-213억, -57%</strong>) · 오딘 지속 하락, 후속작 부재"),
            ('넷마블', "'22 220억 → '25 466억 피크 → '26.1Q 174억 · 전후 216→407 (<strong>+191억, +88%</strong>) · 뱀피르·SK Re:BIRTH 신작 효과, 변동성 큼"),
            ('넥슨', "'22 484억 → '26.1Q 759억 · 전후 398→533 (<strong>+135억, +34%</strong>) · MapleStory Idle 26.1Q 487억 단일 견인"),
            ('NHN', "'22 86억 → '26.1Q 136억 · 전후 108→131 (<strong>+23억, +21%</strong>) · 웹보드 3종 4년 연속 성장, 변동성 최저"),
            ('요점', 'TOP5 합계 정체의 실상은 <strong>엔씨·카카오 감소(-493억)를 넷마블·넥슨·NHN 성장(+349억)이 부분 상쇄</strong>한 결과. 감소액 1위는 엔씨, 감소율 1위는 카카오'),
        ],
    },
    {
        'id': 'kr-3',
        'section': 'KR',
        'headline': 'KR MMORPG 붕괴 공간 — 중화권 Strategy와 KR 비MMORPG RPG가 분할 흡수',
        'interpretation': '퍼블리셔별 매출 이동을 <strong>퍼블 국적 × 장르</strong> 축에서 분해하면 구조가 명확히 드러남. <strong>KR 퍼블 × MMORPG가 1,756 → 650억/월로 -376억 붕괴</strong> (리니지 시리즈 전반 노후화). 이 공간은 두 주체가 분할 흡수:<br><br>① <strong>중화권 × Strategy: 220 → 851억, +591억</strong> (Last War·Whiteout·Kingshot 등 Survival 타이틀)<br>② <strong>KR 퍼블 × 비MMORPG RPG: 318 → 719억, +243억</strong> (MapleStory Idle·SK Re:BIRTH 등 신작)<br><br>주목할 점은 <strong>KR 퍼블 × Strategy는 24 → 60억, +18억에 불과</strong>하다는 것. KR 퍼블은 Strategy 장르로 대응하지 못하고 비MMORPG RPG 쪽으로 방향 전환. Strategy 장르 성장은 실질적으로 <strong>중화권 퍼블의 독점 영역</strong>이며, 이것이 앞서 확인한 해외 퍼블 +66% 성장의 주 경로.',
        'chart': line_chart_multi([
            {'name':'KR × MMORPG',       'color':'#dc2626', 'values':[1756, 1743, 1431, 1421, 650]},
            {'name':'중화권 × Strategy',   'color':'#f59e0b', 'values':[ 220,  300,  782, 1069, 851]},
            {'name':'KR × 비MMORPG RPG', 'color':'#3b82f6', 'values':[ 318,  227,  192,  432, 719]},
            {'name':'KR × Strategy',     'color':'#94a3b8', 'values':[  24,   12,   14,   29,  60]},
        ], ['2022','2023','2024','2025','26.1Q'],
           title='KR 시장 — 퍼블 국적 × 장르 월평균 매출 (억/월)',
           y_max=2000, y_step=500, unit=''),
        'evidence': [
            ('KR × MMORPG', "'22 1,756억 → '26.1Q 650억 · <strong>-376억 (-26%)</strong> · 리니지M·Lineage W·리니지2M 전반 노후화"),
            ('KR × 비MMORPG RPG', "'22 318억 → '26.1Q 719억 · <strong>+243억 (+126%)</strong> · MapleStory Idle·Seven Knights Re:BIRTH·Chaos Zero Nightmare 등 신작 급부상"),
            ('중화권 × Strategy', "'22 220억 → '26.1Q 851억 · <strong>+591억 (+287%)</strong> · Last War·Whiteout·Kingshot Survival 타이틀"),
            ('KR × Strategy', "'22 24억 → '26.1Q 60억 · +18억 (미미) · <strong>KR 퍼블은 Strategy로 사실상 진입하지 못함</strong>"),
            ('중화권 × MMORPG', "'22 231억 → '26.1Q 74억 · -53억 · 중화권도 RPG 양산 모델 하락"),
            ('요점', 'KR 퍼블 MMORPG 붕괴 공간은 <strong>중화권 Strategy(+591) + KR 비MMORPG RPG(+243)</strong>가 분할 흡수. Strategy 장르 성장은 <strong>중화권 독점 영역</strong>이며 KR 퍼블은 해당 장르 대응 실패'),
        ],
    },
    {
        'id': 'kr-5',
        'section': 'KR',
        'headline': 'MAU 감소·ARPMAU 상승 — 고과금 유저 중심 구조',
        'interpretation': '퍼블·장르 재편이 진행되는 동안 수요 축에서도 구조 변화가 동반됨. <strong>MAU는 월평균 4,014만 → 3,615만 (-10%)</strong>으로 유저 기반 축소, 반면 <strong>ARPMAU는 10,328원 → 12,873원 (+25%)</strong>로 유저당 결제 단가 상승. 즉 시장 매출 +13% 성장은 <strong>신규 유입 확대가 아닌 기존 고과금 유저 LTV 확대</strong>에 기인한 것으로 해석됨 (매출 = MAU × ARPMAU ≈ -10% × +25% ≈ +13%).',
        'chart': line_chart([
            {'name':'MAU', 'color':'#3b82f6', 'values':[4291, 4090, 3661, 3619, 3599]},
        ], ['22','23','24','25','26.1Q'], title='KR TOP100 월평균 MAU (만 명)', y_max=5000, unit='만')
        + line_chart([
            {'name':'ARPMAU', 'color':'#f59e0b', 'values':[8938, 9787, 12258, 13263, 11312]},
        ], ['22','23','24','25','26.1Q'], title='KR TOP100 월평균 ARPMAU (원)', y_max=15000, unit='원'),
        'evidence': [
            ('MAU 연도별(만)', "'22 4,291 → '23 4,090 → '24 3,661 → '25 3,619 → '26.1Q 3,599"),
            ('MAU 전후', '4,014만 → 3,615만 (<strong>-399만, -10%</strong>)'),
            ('ARPMAU 연도별(원)', "'22 8,938 → '23 9,787 → '24 12,258 → '25 13,263 → '26.1Q 11,312"),
            ('ARPMAU 전후', '10,328원 → 12,873원 (<strong>+2,545원, +25%</strong>)'),
            ('검증', 'MAU -10% × ARPMAU +25% ≈ 매출 +13% · kr-1 시장 성장률과 정합'),
            ('요점', '유저 기반 축소 + 결제 단가 상승 — <strong>고과금 유저 중심 구조</strong> 심화'),
        ],
    },
    {
        'id': 'kr-6',
        'section': 'KR',
        'headline': 'KR TOP100 신규 진입 수 감소 — 월 8.5 → 6.9개 (-18%) · 중화권은 장르 전환, KR은 방향성 부재',
        'interpretation': '유저 기반 축소·고과금화라는 수요 구조에 대응해 공급 측도 축소. <strong>KR TOP100 월평균 신규 진입 수 8.5개(22) → 6.9개(25), -18%</strong>.<br><br>퍼블 국적별로는 <strong>KR·중화권 모두 투입량 감소</strong>하지만, 장르 구성 변화는 반대 방향. <strong>중화권은 RPG 2.5 → 1.8개(-28%)로 줄이면서 Strategy 0.4 → 0.5개 · Casual 0 → 0.3개로 비RPG 확대 전환 대응</strong> (Last War·Whiteout·Kingshot 등 Survival 장르). 반면 <strong>KR 퍼블은 RPG 2.5 → 1.9개 감소만 진행, Strategy·Casual은 0.4개로 정체</strong> — 장르 재배치 없이 주력 RPG 투입량만 축소.<br><br><strong>보고 시사점</strong>: KR 퍼블의 신작 공급 감소는 단순 "물량 축소"가 아니라 <strong>장르 포트폴리오 재배치 부재</strong>. 중화권이 양산 RPG 실패 경험을 Strategy·Casual로 축 이동한 반면, KR 퍼블은 기존 MMORPG 중심 구조 유지. 신작 검토 시 <strong>장르 다각화가 선결 조건</strong>.',
        'chart': line_chart([
            {'name':'전체 신규 진입', 'color':'#dc2626', 'values':[8.5, 8.1, 8.0, 6.9]},
        ], ['2022','2023','2024','2025'],
           title='① KR TOP100 월평균 신규 진입 수 — 전체 추이 (개/월) · 8.5 → 6.9 (-18%)',
           y_max=10, unit='개')
        + stacked_bar_yearly([
            {'name':'RPG',       'color':'#dc2626', 'values':[2.5, 2.6, 2.2, 1.8, 2.0]},
            {'name':'Strategy',  'color':'#f59e0b', 'values':[0.4, 0.9, 0.5, 0.5, 0.5]},
            {'name':'Casual',    'color':'#10b981', 'values':[0.0, 0.3, 0.3, 0.3, 0.0]},
            {'name':'기타',       'color':'#94a3b8', 'values':[0.6, 0.4, 1.1, 0.4, 1.3]},
        ], ['2022','2023','2024','2025','26.1Q'], title='② 중화권 퍼블 신규 진입 장르 구성 (개/월) — RPG 줄이고 Strategy·Casual 확대', unit='개', decimals=1)
        + stacked_bar_yearly([
            {'name':'RPG',       'color':'#dc2626', 'values':[2.5, 2.2, 1.8, 1.9, 2.0]},
            {'name':'Strategy',  'color':'#f59e0b', 'values':[0.3, 0.2, 0.0, 0.3, 0.0]},
            {'name':'Casual',    'color':'#10b981', 'values':[0.1, 0.1, 0.2, 0.1, 0.1]},
            {'name':'기타',       'color':'#94a3b8', 'values':[0.3, 0.7, 1.4, 0.2, 0.4]},
        ], ['2022','2023','2024','2025','26.1Q'], title='③ KR 퍼블 신규 진입 장르 구성 (개/월) — 전 장르 정체·감소, 전환 없음', unit='개', decimals=1)
        + mini_table(
            ['구분', "'22", "'23", "'24", "'25", '변화', '해석'],
            [
                ['<strong>전체 월평균</strong>', '8.5개', '8.1개', '8.0개', '<strong>6.9개</strong>', '<span style="color:#dc2626;">-18%</span>', '시장 포화 · 공급 축소'],
                ['KR 퍼블', '3.2', '3.2', '3.4', '2.5', '<span style="color:#dc2626;">-22%</span>', '전 장르 감소 (RPG 2.5→1.9, Strategy 0.3 유지)'],
                ['├ KR × RPG',       '2.5', '2.2', '1.8', '1.9', '<span style="color:#64748b;">-24%</span>', 'MMORPG 중심 유지, 비MMORPG는 소폭'],
                ['├ KR × Strategy·Casual', '0.4', '0.3', '0.2', '0.4', '<span style="color:#64748b;">정체</span>', '실질적 전환 시도 없음'],
                ['중화권', '3.5', '4.2', '4.1', '3.0', '<span style="color:#dc2626;">-15%</span>', 'RPG 감소, 비RPG 전환 성공'],
                ['├ 중화권 × RPG',       '2.5', '2.6', '2.2', '<strong>1.8</strong>', '<span style="color:#dc2626;">-28%</span>', '양산 RPG 철수'],
                ['├ 중화권 × Strategy·Casual', '0.4', '1.2', '0.8', '<strong>0.8</strong>', '<span style="color:#059669;">+100%</span>', 'Last War·Whiteout·Kingshot'],
                ['기타 (북미·글로벌)', '0.5', '0.7', '0.5', '1.2', '<span style="color:#059669;">+100%</span>', 'Puzzle·Adventure 등 다변화'],
            ], accent='#0085ca'),
        'evidence': [
            ('전체 월평균 진입', "'22 8.5개 → '25 6.9개 (<strong>-18%</strong>) · 시장 포화로 신작 공급 자체 축소"),
            ('KR 퍼블', "3.2 → 2.5 (-22%) · RPG 2.5→1.9 감소, Strategy 0.3·Casual 0.1 정체 — <strong>RPG 투입만 축소, 장르 재배치 없음</strong>"),
            ('중화권', "3.5 → 3.0 (-15%) · <strong>RPG 2.5→1.8 (-28%)</strong>, <strong>Strategy·Casual 0.4→0.8 (+100%)</strong> — 장르 축 이동 명확"),
            ('기타', "0.5 → 1.2 (+100%) · Puzzle·Adventure·Sim 등 다양화, 비중은 작지만 증가세"),
            ('중화권 전환 대표작', "Strategy: Last War(591억)·Whiteout Survival·Kingshot · Casual: Tasty Travels·Wittle Defender 등"),
            ('NHN 함의', 'KR 퍼블 전체가 <strong>"신작 수만 줄이고 장르 믹스는 그대로"</strong>인 상황. 웹보드 외 신작 검토 시 <strong>장르 다각화가 차별화 포인트</strong> — MMORPG 의존 포트폴리오를 답습하지 않는 설계 필요'),
            ('요점', '물량 축소(-18%)는 공통이나 <strong>장르 포트폴리오 재배치는 중화권만 성공</strong>. KR 퍼블은 방향성 부재 — 시장 구조 변화에 대응한 장르 전환이 신작 성공의 선결 조건'),
        ],
    },
    {
        'id': 'kr-7',
        'section': 'KR',
        'headline': '생존율 구조 — 중화권 RPG 붕괴(57%→30%), KR MMORPG 방어(88%→70%), 비MMORPG 영역이 실제 기회',
        'interpretation': '신규 진입 전체 생존율은 44% → 48%로 안정이지만, 장르 × 퍼블 국적 세분 시 구조 차이가 뚜렷. <strong>중화권 RPG 57% → 30% (-27%p) 꾸준한 붕괴</strong>는 양산형 서브컬처·방치 RPG의 효율 하락을 의미. 반면 <strong>중화권 비RPG(Strategy·Casual)는 50% → 63%로 오히려 상승</strong> — Last War·Whiteout·Kingshot 등 Survival 계열이 장르 전환을 성공시킴.<br><br>KR 퍼블 내부는 또 다른 양상. <strong>MMORPG는 88% → 70%로 여전히 최상위 생존율</strong>(리니지·HIT2·AION2·뱀피르·RF 온라인 넥스트 등 IP 영향력 잔존). 동시에 <strong>비MMORPG RPG 영역(MapleStory Idle·Seven Knights Re:BIRTH·Chaos Zero Nightmare)이 25년 62.5%로 회복</strong>하며 새로운 성장 축으로 부상. 진입 수는 적지만 생존율 회복 폭이 최대.<br><br><strong>보고 시사점</strong>: (a) 중화권 양산 RPG는 더 이상 KR 시장에서 안전지대가 아님, (b) KR MMORPG는 IP 기반으로 방어 가능하나 신규 IP 진입 여지 제한, (c) <strong>실제 확장 기회는 KR × 비MMORPG RPG(Idle·방치·서브컬처·캐릭터 기반)</strong> 영역. NHN이 비웹보드 신작 검토 시 우선 고려 영역.',
        'chart': line_chart_multi([
            {'name':'중화권 RPG',          'color':'#dc2626', 'values':[57.1, 48.3, 45.8, 30.0]},
            {'name':'중화권 비RPG',         'color':'#10b981', 'values':[50.0, 53.8, 62.5, 62.5]},
            {'name':'KR × MMORPG',        'color':'#1e40af', 'values':[87.5, 83.3, 66.7, 70.0]},
            {'name':'KR × 비MMORPG RPG',  'color':'#0085ca', 'values':[25.0, 50.0,  0.0, 62.5]},
        ], ['2022','2023','2024','2025'], title='KR TOP100 신규 진입 3개월 생존율 — 퍼블 국적 × 장르 (%)',
           y_max=100, y_step=20, unit='%')
        + mini_table(
            ['장르 × 퍼블', "'22", "'23", "'24", "'25", '추이·대표 사례'],
            [
                ['중화권 RPG',        '57% (16/28)', '48% (14/29)', '46% (11/24)', '<strong>30% (6/20)</strong>', '<span style="color:#dc2626;">꾸준한 하락</span> · 양산 서브컬처·방치 RPG 실패 증가'],
                ['중화권 비RPG',       '50% (2/4)',   '54% (7/13)',  '63% (5/8)',   '<strong>63% (5/8)</strong>',  '<span style="color:#059669;">안정 양호</span> · Last War·Whiteout·Kingshot 성공'],
                ['KR × MMORPG',     '88% (7/8)',   '83% (10/12)', '67% (10/15)', '<strong>70% (7/10)</strong>', '<span style="color:#1e40af;">최상위 방어</span> · HIT2·나이트 크로우·AION2·뱀피르·RF 온라인 넥스트'],
                ['KR × 비MMORPG RPG','25% (1/4)',   '50% (3/6)',   '0% (0/4)',    '<strong>63% (5/8)</strong>', '<span style="color:#059669;">25년 회복</span> · MapleStory Idle·Seven Knights Re:BIRTH·Chaos Zero Nightmare'],
                ['KR × Strategy·Casual','33% (5/15)','42% (5/12)', '50% (3/6)',  '17% (1/6)',                  '<span style="color:#64748b;">변동 · 모수 작음</span> · NHN 우파루 오딧세이 성공 사례'],
            ], accent='#0085ca'),
        'evidence': [
            ('중화권 RPG', "'22 57% → '25 30% (-27%p) · 20개 진입 중 6개만 생존. 서머너즈워 크로니클·뮤 오리진 류 양산 모델 실패 확산"),
            ('중화권 비RPG', "'22 50% → '25 63% (+13%p) · Last War(591억), Whiteout Survival(Century Games), Kingshot 등 Strategy 장르 Survival 계열이 주도"),
            ('KR × MMORPG', "'22 88% → '25 70% · 진입 수 8→10개 유지, 생존율 최상위. 리니지M·HIT2·나이트 크로우·AION2 등 IP 기반"),
            ('KR × 비MMORPG RPG', "'22 25% → '25 63% (+38%p) · <strong>최대 회복 영역</strong>. MapleStory Idle RPG(26.1Q 487억), Seven Knights Re:BIRTH, Chaos Zero Nightmare 등"),
            ('KR × Strategy·Casual', "'22 33% → '25 17% · 모수 작음(6개). NHN 우파루 오딧세이(23년 Simulation) 생존은 비웹보드 가능성 검증 사례"),
            ('NHN 함의', '중화권 RPG·KR MMORPG 모두 신규 진입 영역 아님. 실제 성장 가능 장르는 <strong>KR × 비MMORPG RPG(Idle·방치·IP 기반 캐릭터 RPG)</strong>와 Strategy·Casual(중화권 외 경쟁 영역)'),
            ('요점', '장르 × 퍼블 국적 매트릭스에서 <strong>"방어 영역(KR MMORPG)" · "확장 영역(KR 비MMORPG RPG)" · "포화 영역(중화권 RPG)"</strong>이 분리됨. 신작 검토는 확장 영역 우선'),
        ],
    },

    # JP
    {
        'id': 'jp-1',
        'section': 'JP',
        'headline': '일본은 정체 — 자국 IP 노후화로 -4%',
        'interpretation': '표면적으로는 -4% 감소이나, 세부적으로 <strong>JP 자국 퍼블 -13% (-748억/월) 하락</strong>. 15년 이상 유지된 대표 IP가 공통적으로 매출 하락 중인 <strong>세대 교체 미흡 상태</strong>.',
        'chart': bar_compare([
            ('모스터스트라이크', -259, '#dc2626', 'XFLAG'),
            ('우마무스메', -238, '#dc2626', 'Cygames'),
            ('Pokémon TCG Pocket', -192, '#dc2626', 'Pokémon'),
            ('Fate/Grand Order', -101, '#dc2626', 'Aniplex'),
            ('프로야구 스피리츠A', -98, '#dc2626', 'KONAMI'),
        ], title='JP 자국 퍼블 IP 쇠락 TOP 5 (억/월 감소)'),
        'evidence': [
            ('요점', 'JP 자국 퍼블 -748억 = KR 카카오게임즈 -214억의 3.5배 충격'),
        ],
    },
    {
        'id': 'jp-2',
        'section': 'JP',
        'headline': '일본 중화권 점유율 상승 — KR 대비 완만한 속도',
        'interpretation': '중화권 +13% 성장으로 JP 자국 하락분(-748억)의 <strong>약 절반 상쇄</strong>. KR(49%) 대비 속도는 느리나 JP도 <strong>중화권 침투 진행 중</strong>. 일본 시장 진입 장벽으로 속도는 상대적으로 완만.',
        'chart': '',
        'evidence': [
            ('중화권 매출', '2,669 → 3,027억 (+358억, +13%)'),
            ('JP 점유율', "'22 62.9% → '26.1Q 51.4% (-11.5%p)"),
            ('중화권 점유율', "'22 25.9% → '26.1Q 34.8% (+8.9%p)"),
            ('요점', 'KR 퍼블은 3.1% → 0.9%로 <strong>거의 퇴출</strong> — NHN 진입 허들 상승'),
        ],
    },
    {
        'id': 'jp-3',
        'section': 'JP',
        'headline': 'JP 1위 매출 -42% 축소 · 중위권은 유지',
        'interpretation': 'JP 1위 게임이 <strong>748억(22) → 470억(25)로 축소</strong>. 중위권은 유지 상태인 점을 고려하면 <strong>신규 히트 타이틀 부재 상태에서 기존 IP만 점진적으로 매출이 하락하는</strong> 구조. 시장 성장 동력 약화 신호.<br><br>로그 스케일 기준 1위 라인만 큰 폭 하락하며 10~100위는 유지 → <strong>상위권 매출 감소가 전체 시장 축소의 주원인</strong>.',
        'chart': rank_line_chart(
            {
                '1위':   [748, 640, 559, 470, 433],
                '10위':  [213, 190, 235, 219, 223],
                '20위':  [105, 111, 139, 127, 131],
                '50위':  [62, 47, 58, 52, 54],
                '100위': [40, 26, 29, 59, 35],
            },
            ['2022', '2023', '2024', '2025', '26.1Q'],
            country_color='#ef4444',
            title='JP 순위별 매출 추이 (로그 스케일, 억/월)',
        ) + mini_table(
            ['순위', '22년', '23년', '24년', '25년', '26.1Q'],
            [
                ('1위', '748', '640', '559', '470', '433'),
                ('10위', '213', '190', '235', '219', '223'),
                ('20위', '105', '111', '139', '127', '131'),
                ('50위', '62', '47', '58', '52', '54'),
                ('100위', '40', '26', '29', '59', '35'),
            ]
        ),
        'evidence': [
            ('1위 변화', '748 → 433억 (-42%) · 유일하게 큰 폭 하락'),
            ('10위 변화', '213 → 223억 (+5%) · 제자리'),
            ('50위 변화', '62 → 54억 (-13%) · 소폭 하락'),
            ('100위 변화', '40 → 35억 (-13%) · 소폭 하락'),
            ('요점', '<strong>상위권만 붕괴, 중위권은 제자리</strong> → 시장 에너지 감소 신호 · 메가히트 부재'),
        ],
    },

    # US
    {
        'id': 'us-1',
        'section': 'US',
        'headline': '미국 시장 +17% 성장 · 월평균 +2,935억 증가',
        'interpretation': 'KR·JP가 정체/축소되는 기간 중 US는 <strong>월 +2,935억 순증가</strong>. 매출 규모 자체가 KR의 4배 이상. <strong>성장 시장 진입 또는 축소 시장 방어</strong> 중 전략 선택 필요.',
        'chart': before_after_bars([
            ('KR 시장', 4109, 4654, '#3b82f6'),
            ('JP 시장', 9306, 8969, '#ef4444'),
            ('US 시장', 16801, 19736, '#a855f7'),
        ], title='3국 시장 규모 — 25년 전후 (억/월)'),
        'evidence': [
            ('US 100위 규모', '43~86억/월 ≈ <strong>KR 20위 수준</strong>'),
            ('요점', 'US 중위권 = KR 상위권. 진입만 하면 3~4배 매출 잠재력'),
        ],
    },
    {
        'id': 'us-2',
        'section': 'US',
        'headline': 'US 성장 중 중화권 기여 70% · Last War 단독 +316억',
        'interpretation': 'US 성장분 +2,935억 중 중화권이 <strong>+2,065억 (70% 기여)</strong>. 단일 게임 <strong>Last War:Survival</strong>이 409 → 725억 (+316억) 기록. <strong>KR·US 공통 성장 타이틀</strong>.',
        'chart': before_after_bars([
            ('Last War (FUNFLY)', 409, 725, '#f59e0b'),
            ('Royal Match (Dream)', 624, 904, '#10b981'),
            ('MONOPOLY GO!', 1384, 1061, '#dc2626'),
        ], title='US 대표 게임 — 25년 전후 매출 변화 (억/월)'),
        'evidence': [
            ('요점', '중화권 1개 게임이 시장 단독 +316억 견인'),
        ],
    },
    {
        'id': 'us-3',
        'section': 'US',
        'headline': 'US 시장은 진입 장벽이 높고 생존율도 높음 — 고수율 구조',
        'interpretation': 'US의 TOP100 월평균 신규 진입은 <strong>2.4 → 3.0개</strong>로 KR(월 7~8개)·JP(월 4~6개) 대비 매우 낮음. 반면 <strong>3개월 생존율은 60~78%</strong>로 3국 중 최고 수준 (KR 37~49%, JP 36~48%).<br><br>시사점은 <strong>"진입 장벽이 높은 대신 한번 안착하면 장기 생존이 가능한 구조"</strong>. 연 단위 진입 기회는 적지만 ROI 관점에서는 가장 안정적인 시장.',
        'chart': line_chart_multi([
            {'name':'US 월평균 진입', 'color':'#a855f7', 'values':[2.4, 1.8, 2.3, 2.5, 3.0]},
            {'name':'KR 참고',        'color':'#cbd5e1', 'values':[8.5, 8.2, 7.5, 6.9, 6.5]},
            {'name':'JP 참고',        'color':'#fca5a5', 'values':[6.0, 4.0, 4.0, 3.6, 1.5]},
        ], ['2022','2023','2024','2025','26.1Q'],
           title='3국 월평균 신규 진입 수 비교 (개/월)',
           y_max=10, y_step=2, unit='개'),
        'evidence': [
            ('US 월평균 진입', "'22 2.4 → '25 2.5개 · 안정적"),
            ('US 3개월 생존율', "'22 73% → '23 65% → '24 60% → '25 77.8%"),
            ('KR 생존율 대비', '37~49% — US 대비 약 30%p 낮음'),
            ('JP 생존율 대비', '36~48% — US 대비 약 30%p 낮음'),
            ('요점', 'US는 <strong>저빈도 진입 + 고생존율</strong> 구조. 진입 자원을 집중 투자할 가치 있는 시장'),
        ],
    },
    {
        'id': 'us-4',
        'section': 'US',
        'headline': '기타 그룹(글로벌 스튜디오) 우세 — 북미 자국 퍼블은 생존율 하락',
        'interpretation': 'US 내 퍼블리셔 구조도 재편 중. <strong>기타 그룹(핀란드 Supercell, 이스라엘 Playtika, 터키 Dream Games 등 글로벌 스튜디오)이 물량 23% → 48%로 최대 비중</strong>. 생존율도 83% → 92%로 최고 수준 유지.<br><br>반면 <strong>북미 자국 퍼블은 물량 38% → 18%로 감소</strong>, 생존율도 80% → 40%로 <strong>반토막 수준</strong>. 중화권은 24년 44% 피크 후 26%로 조정되었으나 생존율은 71%로 비교적 안정.',
        'chart': line_chart_multi([
            {'name':'기타 (글로벌)', 'color':'#059669', 'values':[83.3, 60.0, 77.8, 92.3]},
            {'name':'북미 자국',      'color':'#dc2626', 'values':[80.0, 66.7, 50.0, 40.0]},
            {'name':'중화권',         'color':'#f59e0b', 'values':[57.1, 83.3, 54.5, 71.4]},
        ], ['2022','2023','2024','2025'],
           title='US 퍼블 그룹별 3개월 생존율 (%)',
           y_max=100, y_step=25, unit='%'),
        'evidence': [
            ('기타 그룹 물량', "'22 23% → '25 48% (비중 최대)"),
            ('북미 자국 물량', "'22 38% → '25 18% (감소)"),
            ('중화권 물량', "'22 27% → '24 44% 피크 → '25 26%"),
            ('기타 그룹 생존율', "'22 83% → '25 92% (최고 수준)"),
            ('북미 자국 생존율', "'22 80% → '25 40% (하락)"),
            ('요점', 'US에서는 <strong>글로벌 스튜디오(핀란드·이스라엘·터키)</strong>가 북미 자국 퍼블을 추월. 신작 출시 벤치마크는 이 그룹이 기준'),
        ],
    },

    # COMMON
    {
        'id': 'common-1',
        'section': 'COMMON',
        'headline': '중화권 퍼블리셔 점유율 상승은 3국 공통 현상',
        'interpretation': '<strong>3국 공통으로 나타나는 현상</strong>. KR +16%p, JP +9%p, US +11%p. 중화권 퍼블리셔가 <strong>3국에서 동시 점유율 확보</strong> — 한국 한정 현상이 아닌 글로벌 구조 변화.',
        'chart': line_chart([
            {'name':'KR', 'color':'#3b82f6', 'values':[21.8, 25.5, 35.8, 36.9, 37.7]},
            {'name':'JP', 'color':'#ef4444', 'values':[25.9, 26.7, 31.8, 32.5, 34.8]},
            {'name':'US', 'color':'#a855f7', 'values':[15.5, 13.8, 15.4, 22.3, 26.8]},
        ], ['22', '23', '24', '25', '26.1Q'], title='3국 중화권 점유율 추이 (%)', y_max=50, unit='%'),
        'evidence': [
            ('3국 중화권 합계 증가', '+3,003억/월 (+46%)'),
            ('요점', '중화권 1개 퍼블리셔(FUNFLY 등)가 3국 시장 동시 흔드는 구도'),
        ],
    },
    {
        'id': 'common-2',
        'section': 'COMMON',
        'headline': 'MAU 감소 · ARPMAU 상승은 3국 공통 구조',
        'interpretation': 'MAU 감소에도 매출이 증가하는 구조는 <strong>글로벌 모바일 게임 시장의 공통 현상</strong>. 신규 유입 의존 모델의 한계. <strong>기존 유저 LTV 확대 + 고가 상품(50만원+ 패키지) 구축</strong>이 핵심 과제.',
        'chart': '',
        'evidence': [
            ('3국 MAU', '4,014만 → 3,615만 (-10%)'),
            ('3국 ARPMAU', '10,328 → 12,873원 (+25%)'),
            ('3국 DL', '582 → 539만건 (-7%)'),
            ('요점', '신규 유입 ↓ but 단가 ↑ → <strong>고래 유저화</strong> 시대'),
        ],
    },

    # WEBBOARD
    {
        'id': 'wb-1',
        'section': 'WEBBOARD',
        'headline': '웹보드 시장 +22% 성장 — 일반 시장(+13%) 대비 1.6배',
        'interpretation': '일반 게임 시장 +13% 성장 기간 중 웹보드는 <strong>+22% 성장</strong>. 규제 시장 내에서도 성장 지속. 원인은 <strong>ARPMAU가 일반 시장 대비 16% 높은 수준</strong> — 소수 고과금 유저의 결제 밀도가 높음.',
        'chart': before_after_bars([
            ('KR 일반 시장', 4109, 4654, '#3b82f6'),
            ('KR 웹보드', 137, 168, '#0085ca'),
        ], title='KR 일반 vs 웹보드 시장 성장 (억/월)'),
        'evidence': [
            ('웹보드 ARPMAU', '15,429원 (일반 13,263원의 1.16배)'),
            ('요점', '규제 시장 + 고래 유저 + 중독성 → 매출 효율 일반 시장 추월'),
        ],
    },
    {
        'id': 'wb-2',
        'section': 'WEBBOARD',
        'headline': 'NHN 웹보드 점유율 74% 유지',
        'interpretation': 'KR 메인 시장이 재편되는 중에도 NHN은 <strong>웹보드 내 점유율 74%로 주도적 지위 유지</strong>. 네오위즈 15%대 대비 <strong>4~5배 격차</strong>. 해당 도메인은 NHN의 프리미엄 영역.',
        'chart': line_chart([
            {'name':'NHN', 'color':'#0085ca', 'values':[62.7, 73.7, 76.4, 79.1, 68.7]},
            {'name':'네오위즈', 'color':'#ff6b35', 'values':[23.5, 20.8, 19.1, 17.3, 15.4]},
            {'name':'Zempot WPL', 'color':'#8b5cf6', 'values':[0.4, 0.0, 0.0, 3.0, 9.4]},
        ], ['22', '23', '24', '25', '26.1Q'], title='웹보드 퍼블리셔별 점유율 (%)', y_max=90, unit='%'),
        'evidence': [
            ('요점', 'NHN 점유율 4배 격차 유지 · WPL 26.1Q 급부상'),
        ],
    },
    {
        'id': 'wb-3',
        'section': 'WEBBOARD',
        'headline': 'NHN 3종 TOP100 51개월 연속 체류 · 매출 +8~+44% 성장',
        'interpretation': '한게임 포커·섯다&맞고·포커클래식 <strong>3종 모두 TOP 100 51개월 전 기간 연속 체류</strong>. 일반 게임 12개월 생존율(40%) 대비 웹보드는 별도 카테고리로 분류 가능.',
        'chart': '',
        'evidence': [
            ('한게임 포커', '40 → 43억 (+8%) · 51개월 무중단'),
            ('한게임 섯다&맞고', '27 → 39억 (+44%) · 51개월 무중단'),
            ('한게임포커 클래식', '27 → 34억 (+26%) · 51개월 무중단'),
            ('한게임 신맞고', '9 → 10억 (+3%) · 51개월 무중단'),
            ('요점', '3종 모두 <strong>무중단 + 성장</strong> = 포트폴리오의 강인함'),
        ],
    },
    {
        'id': 'wb-4',
        'section': 'WEBBOARD',
        'headline': 'WPL(Zempot) 매출 5배 상승 — 신흥 경쟁자 부상',
        'interpretation': '25년 8월까지 3억대였던 WPL이 <strong>25년 9월 13억으로 상승, 현재 19억대 유지</strong>. 원인은 <strong>오프라인 대회(WPH, 상금 10억)·50만원 이상 고단가 패키지·프로 선수 활용 스포츠 브랜딩</strong>의 복합 효과. 이스포츠 플랫폼 모델로 전환.',
        'chart': line_chart([
            {'name':'WPL', 'color':'#8b5cf6', 'values':[3.2, 3.7, 13.4, 16.2, 19.0]},
        ], ['25.7', '25.8', '25.9', '25.11', '26.3'], title='WPL 월별 매출 급증 (억/월)', y_max=25, unit='억'),
        'evidence': [
            ('급성장 원인', '① 오프라인 대회(WPH) 상금 10억 · ② 50만원+ 고단가 패키지 · ③ 임요환 라이브 콘텐츠 · ④ 리그 상설화'),
            ('요점', '"실력 기반 스포츠" 프레임 — 국내 웹보드 규제(5만원 한도) 우회 + 프리미엄 타겟'),
        ],
    },
    {
        'id': 'wb-5',
        'section': 'WEBBOARD',
        'headline': '네오위즈(피망) 매출 30억대 4년 정체',
        'interpretation': '피망 포커·뉴맞고 합계 <strong>30억대 정체 (2022~2026)</strong>. 광고 유입률이 NHN 대비 1/4~1/5 수준 — <strong>마케팅 투자 축소로 브랜드 영향력 축소</strong>. 해당 영역을 WPL이 확보 중.',
        'chart': before_after_bars([
            ('NHN 포커 광고율', 24.7, 32.1, '#0085ca'),
            ('Pmang Poker 광고율', 11.3, 20.6, '#ff6b35'),
            ('NHN 신맞고 광고율', 42.0, 45.1, '#0085ca'),
            ('피망 뉴맞고 광고율', 8.1, 9.3, '#ff6b35'),
        ], title='광고 유입률 비교 (%) — NHN vs 네오위즈', unit='%'),
        'evidence': [
            ('요점', 'NHN 광고율 2~5배 높음 → 마케팅 공세의 차이'),
        ],
    },

    # STRATEGY
    {
        'id': 'strategy-1',
        'section': 'STRATEGY',
        'headline': 'NHN 핵심 자산 — 웹보드 도메인 주도적 지위',
        'interpretation': 'KR 일반 시장에서는 점유율 방어도 어려운 상황. 반면 NHN은 <strong>웹보드라는 특수 도메인에서 74% 독점</strong>. 규제 시장이라 중화권도 진입 어려움. <strong>웹보드는 NHN의 해자(moat)</strong>.',
        'chart': bar_compare([
            ('NHN 일반 시장 점유율', 3, '#64748b', 'TOP5 중 5위'),
            ('NHN 웹보드 점유율', 74, '#0085ca', '독점적 지위'),
        ], title='NHN 점유율 — 일반 vs 웹보드', unit='%', max_val=100),
        'evidence': [
            ('수명 비교', '일반 12개월 생존율 40% vs <strong>웹보드 NHN 3종 100%</strong>'),
            ('요점', '"일반 게임 확장"보다 "웹보드 강화 + 글로벌 확장"이 효율적'),
        ],
    },
    {
        'id': 'strategy-2',
        'section': 'STRATEGY',
        'headline': 'US 시장 100위 매출 규모 ≈ KR 20위 수준',
        'interpretation': 'US 시장 100위 게임의 월평균 매출이 <strong>43~86억</strong> — KR 20위권 수준. NHN 웹보드의 US 진출 시 <strong>중위권 안착만으로 현재 KR 매출의 2~3배 규모 기대</strong>.',
        'chart': mini_table(
            ['순위', 'KR', 'JP', 'US'],
            [
                ('1위', '510억', '559억', '2,267억'),
                ('10위', '85억', '235억', '329억'),
                ('20위', '48억', '139억', '212억'),
                ('50위', '21억', '58억', '105억'),
                ('100위', '9억', '29억', '62억'),
            ]
        ),
        'evidence': [
            ('요점', 'US 100위 ≈ KR 20위 → 진입만 하면 <strong>3~4배 매출</strong> 가능성'),
        ],
    },

    # ============ 신규 게임 출시 방향성 (3개) ============
    {
        'id': 'launch-1',
        'section': 'STRATEGY',
        'headline': '[신작 장르] Strategy는 중화권 집중 · Puzzle/Casual은 분산 경쟁 구조',
        'interpretation': '최다 성장 장르는 Strategy이나 <strong>중화권이 점유 집중 (FUNFLY Last War, Kingshot 등)</strong>. 후발 진입 시 자본·IP·오퍼레이션 측면 열위 예상. 반면 <strong>Puzzle은 터키(Dream Games)·핀란드(Supercell) 등 분산 경쟁 구조</strong>이며, Casual은 글로벌 퍼블 혼재로 <strong>진입 여지 존재</strong>.',
        'chart': bar_compare([
            ('KR Strategy', 636, '#dc2626', '+123% 중화권 장악'),
            ('KR Puzzle', 194, '#059669', '+97% 분산 구조'),
            ('KR 비MMORPG RPG', 168, '#059669', '+24% 가능성'),
            ('KR Casual', 25, '#059669', '+32% 틈새'),
        ], title='KR 장르별 25년 전후 매출 증가액 (억/월)'),
        'evidence': [
            ('Strategy 중화권 비중', 'KR Strategy 성장의 90%+ = 중화권 게임'),
            ('Puzzle 리더', 'Dream Games(터키), Supercell(핀란드) — 분산'),
            ('요점', '<strong>레드오션 피하고 분산된 장르(Puzzle/Casual) 노리기</strong>가 전략적'),
        ],
    },
    {
        'id': 'launch-2',
        'section': 'STRATEGY',
        'headline': '[타겟 국가] US 직접 진입 대안 — JP 저평가 IP 인수 후 글로벌 재출시',
        'interpretation': 'US 직접 진입은 자본·마케팅 부담 증가 및 경쟁 심화. 대안: <strong>JP 자국 IP가 쇠락 중 (모스터스트라이크 -259억, 우마무스메 -238억 등 대형 IP 매출 반토막)</strong>. 저평가 IP 인수 또는 글로벌 운영 라이선스 확보 후 <strong>NHN 운영 노하우 기반 리브랜딩</strong> 경로. 중화권과 구분되는 차별화 경로.',
        'chart': bar_compare([
            ('모스터스트라이크', -259, '#dc2626', 'XFLAG · 40% 감소'),
            ('우마무스메', -238, '#dc2626', 'Cygames · 45% 감소'),
            ('Pokémon TCG Pocket', -192, '#dc2626', 'Pokémon · 38% 감소'),
            ('Fate/Grand Order', -101, '#dc2626', 'Aniplex · 21% 감소'),
        ], title='쇠락 중인 JP 자국 IP — 글로벌 재활 기회 (억/월 감소)'),
        'evidence': [
            ('JP 자국 퍼블 점유율', '62.9% → 51.4% (-11.5%p)'),
            ('쇠락 IP 특성', '팬덤/IP 자산 있음 + 운영 노후화 + 글로벌 확장 부진'),
            ('NHN 차별화', '<strong>웹보드 운영 노하우 (리텐션·결제 최적화)</strong>를 IP 게임에 이식'),
            ('요점', '"US 정면 돌파" 대신 "<strong>JP 저평가 IP 인수 + 글로벌 재출시</strong>"가 자본 효율적'),
        ],
    },
    {
        'id': 'launch-3',
        'section': 'STRATEGY',
        'headline': '[퍼블 협업] 중화권 제휴 대안 — 스포츠·리그 플랫폼 IP 연계',
        'interpretation': '중화권 Publishing 제휴는 <strong>매출 분배 및 중화권 의존도 증가</strong> 리스크 존재. 대안: <strong>WPL 사례에서 검증된 스포츠/리그 프레임</strong>. 한국 웹보드 규제(5만원 한도) 우회 및 프리미엄 고과금 유저 타겟. NHN 웹보드 자산과 스포츠 이벤트 IP 결합이 유효한 접근.',
        'chart': '',
        'evidence': [
            ('WPL 성장 사례', '25.9월 3.7 → 19억 (5배) — 오프라인 대회 + 고단가 BM 전략'),
            ('스포츠 브랜딩 효과', '임요환 등 프로 선수 활용 → 고과금 유저 확보'),
            ('규제 회피', '"실력 기반 스포츠" 프레임 = 5만원 결제 한도 우회 가능'),
            ('NHN 적용 가능', '포커 토너먼트 + 섯다&맞고 리그 + e스포츠 공동 주최 등'),
            ('요점', 'WPL이 뚫은 길 = NHN도 따라갈 수 있는 로드맵. <strong>웹보드 자산 + 스포츠 IP 결합</strong>'),
        ],
    },
    {
        'id': 'launch-4',
        'section': 'STRATEGY',
        'headline': '[종합 우선순위] 장르·시장·방식 3축 기반 출시 우선순위',
        'interpretation': '앞선 3개 분석 종합: <strong>①장르 Puzzle/Casual ②시장 JP 자국 IP 인수 + US 추후 진출 ③방식 스포츠/리그 플랫폼 확장</strong>. 리스크·수익 균형을 고려한 우선순위.',
        'chart': mini_table(
            ['우선순위', '방향', '근거', '리스크'],
            [
                ('1순위', '웹보드 리그 플랫폼 확장 (WPL 벤치마크)', '검증된 BM + 규제 우회', '낮음'),
                ('2순위', 'JP 자국 IP 인수 → 글로벌 재출시', 'IP 저평가 + NHN 운영력', '중간 (M&A 실행)'),
                ('3순위', 'Puzzle/Casual 신작 US 진출', '시장 규모 ↑ 경쟁 분산', '높음 (자본 투입)'),
            ]
        ),
        'evidence': [
            ('회피할 선택', '<strong>Strategy 장르 신작</strong> (중화권 레드오션), <strong>중화권 퍼블 Publishing 제휴</strong> (의존 심화)'),
            ('요점', '검증된 도메인(웹보드) 확장 → IP 인수 → 신장르 신작 순으로 <strong>리스크 계단</strong> 구축'),
        ],
    },
]

SECTION_META = {
    'KR':       ('🇰🇷 한국 시장',    '#3b82f6', '#dbeafe'),
    'JP':       ('🇯🇵 일본 시장',    '#ef4444', '#fee2e2'),
    'US':       ('🇺🇸 미국 시장',    '#a855f7', '#f3e8ff'),
    'COMMON':   ('🌏 3국 공통 트렌드', '#64748b', '#f1f5f9'),
    'WEBBOARD': ('🎴 웹보드 심층',   '#0085ca', '#e0f2fe'),
    'STRATEGY': ('🎯 전략 시사점',   '#d97706', '#fef3c7'),
}

BRIDGES = {
    'kr-1': '시장 성장 주체 재편의 규모를 점유율 관점에서 확인',
    'kr-4': 'KR 퍼블 내부 — 감소 주체 세분화',
    'kr-2b': '상대적으로 방어 중인 TOP5 내부의 매출 궤적 분기',
    'kr-2': '퍼블리셔별 매출 이동의 장르 축 분석',
    'kr-3': '재편된 시장에서의 유저 행동·단가 변화',
    'kr-5': '수요 구조 변화에 대응한 신작 공급 조정',
    'kr-6': '공급 감소 환경에서 신작 생존율 변화',
    'jp-1': '자국 퍼블 감소분을 대체하는 주체',
    'jp-2': '시장 성장 동력 변화 (순위별 관점)',
    'us-1': 'US +17% 성장의 단일 최대 기여 요인',
    # 'us-2' 브릿지 제거 — us-3 삭제로 US 섹션 마지막 인사이트가 us-2가 됨
    'common-1': '글로벌 재편 기간 중 사용자 행동 변화',
    'wb-1': '고성장 웹보드 시장 내 NHN의 위치',
    'wb-2': '74% 점유율의 기반 요인',
    'wb-3': '최근 NHN 우위에 영향을 주는 신규 경쟁자 등장',
    'wb-4': '기존 경쟁자 네오위즈의 대응 현황',
    'strategy-1': '경쟁 우위 영역의 확장 방향',
    'strategy-2': '신작 출시 시 장르 선정 방향',
    'launch-1': '진출 시장 선정',
    'launch-2': '진출 방식 선정',
    'launch-3': '3가지 방향의 우선순위 정리',
}

def build_insight(ins, idx_in_section, total_in_section):
    color, bg = SECTION_META[ins['section']][1], SECTION_META[ins['section']][2]
    ev_html = ''
    for label, value in ins['evidence']:
        is_summary = label == '요점'
        cls = 'summary' if is_summary else ''
        icon = '💡 요점' if is_summary else label
        ev_html += f'<li class="evidence-item {cls}"><span class="ev-label">{icon}</span><span class="ev-value">{value}</span></li>'

    chart = ins.get('chart', '')
    chart_html = f'<div class="chart-wrap">{chart}</div>' if chart else ''

    # 순번 배지
    num_badge = f'<span class="insight-num" style="background:{color};">{idx_in_section}</span>'

    insight_html = f'''<details class="insight" id="{ins['id']}" style="--accent:{color}; --bg:{bg};">
  <summary>
    {num_badge}
    <div class="headline">{ins['headline']}</div>
    <div class="expand-hint">근거 보기 ▸</div>
  </summary>
  <div class="body">
    <div class="interpretation">{ins['interpretation']}</div>
    {chart_html}
    <ul class="evidence-list">{ev_html}</ul>
  </div>
</details>'''

    # 브릿지 (다음 인사이트로 이어주는 문구)
    bridge_text = BRIDGES.get(ins['id'])
    if bridge_text and idx_in_section < total_in_section:
        insight_html += f'<div class="bridge" style="--bc:{color};"><span class="bridge-arrow">▼</span><span class="bridge-text">{bridge_text}</span></div>'

    return insight_html

SECTION_INTRO = {
    'KR': '한국 모바일 게임 시장은 25년 전후로 성장했으나 성장 주체가 재편됨. 국내 퍼블리셔 매출과 점유율의 변화, 장르 구조 변화, 신규 진입 물량·생존율을 순차적으로 분석.',
    'JP': '일본 시장은 25년 전후 -4% 축소. 자국 퍼블리셔 매출 하락과 중화권 퍼블리셔 진입 현황을 분석.',
    'US': '미국 시장은 25년 전후 +17% 성장. 성장 기여 구성과 중화권 퍼블리셔 진입 현황을 분석.',
    'COMMON': 'KR·JP·US 3국의 공통 변화 요인을 정리.',
    'WEBBOARD': '웹보드 도메인의 성장률·점유율·수명·게임 포트폴리오 현황을 분석.',
    'STRATEGY': '앞선 분석을 기반으로 한 NHN의 현재 자산 평가와 신규 출시 방향성.',
}

SECTION_SUMMARY = {
    'KR': {
        'title': '🇰🇷 KR 시장 요약',
        'points': [
            ('시장 규모', '월평균 4,109억 → 4,654억 (+13%, +545억). 전체 시장은 성장.'),
            ('성장 주체', '중화권 +568억 단독 기여 (+49%), KR 퍼블 -146억 (-6%), 해외 기타 +62% 증가.'),
            ('KR 퍼블 내부', 'TOP5 매출 +1% 정체, TOP5 외 중소 KR 퍼블 -45%. 카카오게임즈 -57% 단일 변동 폭 최대.'),
            ('점유율 변화', 'KR 퍼블 66.9% → 48.2% (-18.7%p), 중화권 21.8% → 37.7% (+15.9%p).'),
            ('장르 구조', 'MMORPG -436억 감소, Strategy +636억 증가로 장르 교체 진행.'),
            ('유저·단가', 'MAU -16%, ARPMAU +48%. 신규 유입 감소 대비 유저당 결제 단가 상승.'),
            ('신작 공급', '월평균 신규 진입 8.5 → 6.9개 (-18%). 중화권은 RPG 비중 축소, 비RPG 확대로 전환.'),
            ('생존율', '전체 44% → 48% 유지. 중화권 RPG 57% → 30%로 하락, 중화권 비RPG 60%+ 유지.'),
        ],
        'conclusion': 'KR 시장은 성장 중이나 주체 재편과 장르 교체가 동시 진행. 중화권은 RPG 양산 모델 효율 하락에 대응해 Strategy·Casual 중심으로 전환 중.',
    },
}

sections_html = ''
for sec_key in ['KR','JP','US','COMMON','WEBBOARD','STRATEGY']:
    sec_name, color, bg = SECTION_META[sec_key]
    items = [i for i in INSIGHTS if i['section'] == sec_key]
    if not items: continue
    total = len(items)
    ih = ''.join(build_insight(ins, idx+1, total) for idx, ins in enumerate(items))
    intro = SECTION_INTRO.get(sec_key, '')
    # 섹션 요약 박스
    summary_html = ''
    if sec_key in SECTION_SUMMARY:
        s = SECTION_SUMMARY[sec_key]
        pts_html = ''
        for label, val in s['points']:
            pts_html += f'<li><span class="sm-label">{label}</span><span class="sm-val">{val}</span></li>'
        summary_html = f'''
  <div class="section-summary" style="--sc:{color};">
    <div class="section-summary-title">{s["title"]}</div>
    <ul class="section-summary-list">{pts_html}</ul>
    <div class="section-summary-concl">{s["conclusion"]}</div>
  </div>'''

    sections_html += f'''
<div class="section" style="--sec-color:{color}; --sec-bg:{bg};">
  <div class="section-header">
    <div class="section-title">{sec_name}</div>
    <div class="section-count">{total}개 인사이트</div>
  </div>
  <div class="section-intro">{intro}</div>
  {ih}
  {summary_html}
</div>'''

tldr_cards = '''
<div class="tldr-grid">
  <div class="tldr-card" style="--c:#3b82f6;">
    <div class="tldr-label">KR 시장</div>
    <div class="tldr-value">+13%</div>
    <div class="tldr-sub">4,109억 → 4,654억<br>중화권이 단독 견인</div>
  </div>
  <div class="tldr-card" style="--c:#ef4444;">
    <div class="tldr-label">JP 시장</div>
    <div class="tldr-value">-4%</div>
    <div class="tldr-sub">9,306억 → 8,969억<br>자국 IP 노후화</div>
  </div>
  <div class="tldr-card" style="--c:#a855f7;">
    <div class="tldr-label">US 시장</div>
    <div class="tldr-value">+17%</div>
    <div class="tldr-sub">1.68조 → 1.97조<br>Last War 메가히트</div>
  </div>
  <div class="tldr-card" style="--c:#0085ca;">
    <div class="tldr-label">웹보드 시장</div>
    <div class="tldr-value">+22%</div>
    <div class="tldr-sub">137억 → 168억<br>NHN 점유율 74%</div>
  </div>
</div>'''

html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NHN 시장 분석 — 임원 보고용 핵심 인사이트</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Noto Sans KR',sans-serif; background:#f5f7fa; color:#1e293b; padding:40px 20px; line-height:1.6; }}
  .container {{ max-width:1000px; margin:0 auto; }}
  .header {{ background:linear-gradient(135deg,#1e293b,#0f172a); color:#fff; border-radius:14px; padding:32px 36px; margin-bottom:24px; box-shadow:0 4px 16px rgba(0,0,0,0.1); }}
  h1 {{ font-size:1.6rem; font-weight:800; margin-bottom:8px; letter-spacing:-0.5px; }}
  .header .subtitle {{ font-size:0.88rem; color:#cbd5e1; font-weight:400; line-height:1.6; }}
  .header .meta {{ margin-top:12px; padding-top:12px; border-top:1px solid rgba(255,255,255,0.1); font-size:0.78rem; color:#94a3b8; }}
  .tldr-section {{ margin-bottom:28px; }}
  .tldr-label-main {{ font-size:0.82rem; font-weight:700; color:#475569; margin-bottom:12px; display:flex; align-items:center; gap:8px; }}
  .tldr-label-main::before {{ content:""; width:4px; height:16px; background:#0f172a; border-radius:2px; }}
  .tldr-grid {{ display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; }}
  .tldr-card {{ background:#fff; border-radius:10px; padding:16px 18px; border-top:4px solid var(--c); box-shadow:0 2px 8px rgba(0,0,0,0.05); }}
  .tldr-label {{ font-size:0.72rem; color:#64748b; font-weight:600; }}
  .tldr-value {{ font-size:1.8rem; color:var(--c); font-weight:800; margin:4px 0; letter-spacing:-1px; }}
  .tldr-sub {{ font-size:0.68rem; color:#94a3b8; line-height:1.5; }}
  .section {{ margin-bottom:28px; }}
  .section-header {{ display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; padding-bottom:8px; border-bottom:2px solid var(--sec-color); }}
  .section-title {{ font-size:1.15rem; font-weight:800; color:var(--sec-color); }}
  .section-count {{ font-size:0.78rem; color:#94a3b8; font-weight:600; background:var(--sec-bg); padding:3px 10px; border-radius:12px; }}
  .section-intro {{ font-size:0.85rem; color:#475569; line-height:1.6; padding:12px 16px; background:var(--sec-bg); border-radius:8px; margin-bottom:14px; border-left:3px solid var(--sec-color); }}
  .insight {{ background:#fff; border:1px solid #e2e8f0; border-radius:10px; margin-bottom:4px; overflow:hidden; transition:all 0.2s; }}
  .insight[open] {{ box-shadow:0 4px 16px rgba(0,0,0,0.08); border-color:var(--accent); }}
  .insight summary {{ list-style:none; cursor:pointer; padding:18px 22px; display:flex; align-items:center; justify-content:space-between; gap:16px; background:#fff; transition:background 0.2s; }}
  .insight-num {{ display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border-radius:50%; color:#fff; font-weight:800; font-size:0.78rem; flex-shrink:0; }}
  .bridge {{ display:flex; align-items:center; gap:10px; padding:10px 22px 10px 40px; margin:0; font-size:0.8rem; color:#64748b; font-style:italic; position:relative; }}
  .bridge-arrow {{ color:var(--bc); font-size:0.9rem; font-weight:700; font-style:normal; }}
  .bridge-text {{ flex:1; }}
  .bridge::before {{ content:""; position:absolute; left:32px; top:0; bottom:0; width:2px; background:var(--bc); opacity:0.3; }}
  /* 섹션 요약 박스 */
  .section-summary {{ margin-top:20px; background:#fff; border:2px solid var(--sc); border-radius:10px; padding:18px 22px; }}
  .section-summary-title {{ font-size:0.98rem; font-weight:800; color:var(--sc); margin-bottom:12px; padding-bottom:8px; border-bottom:1px dashed var(--sc); }}
  .section-summary-list {{ list-style:none; display:flex; flex-direction:column; gap:6px; margin-bottom:12px; }}
  .section-summary-list li {{ display:grid; grid-template-columns:110px 1fr; gap:12px; font-size:0.82rem; padding:4px 0; border-bottom:1px solid #f1f5f9; }}
  .section-summary-list li:last-child {{ border-bottom:none; }}
  .sm-label {{ color:#64748b; font-weight:600; }}
  .sm-val {{ color:#1e293b; }}
  .section-summary-concl {{ font-size:0.85rem; color:#334155; padding:10px 14px; background:#f8fafc; border-left:3px solid var(--sc); border-radius:0 6px 6px 0; line-height:1.6; }}
  .insight summary::-webkit-details-marker {{ display:none; }}
  .insight summary:hover {{ background:var(--bg); }}
  .insight[open] summary {{ background:var(--bg); border-bottom:1px solid #e2e8f0; }}
  .insight .headline {{ font-size:1rem; font-weight:700; color:#1e293b; flex:1; }}
  .insight .expand-hint {{ font-size:0.75rem; color:var(--accent); font-weight:600; white-space:nowrap; }}
  .insight[open] .expand-hint {{ opacity:0.6; }}
  .insight .body {{ padding:20px 22px; background:#fafbfc; }}
  .interpretation {{ font-size:0.92rem; color:#334155; line-height:1.75; padding:14px 18px; background:#fff; border-left:4px solid var(--accent); border-radius:0 6px 6px 0; margin-bottom:14px; }}
  .interpretation strong {{ color:var(--accent); font-weight:700; }}
  .chart-wrap {{ background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:14px 18px; margin-bottom:14px; }}
  .evidence-list {{ list-style:none; display:flex; flex-direction:column; gap:6px; }}
  .evidence-item {{ display:grid; grid-template-columns:180px 1fr; gap:14px; font-size:0.82rem; padding:8px 12px; background:#fff; border-radius:6px; border:1px solid #f1f5f9; }}
  .evidence-item .ev-label {{ color:#64748b; font-weight:600; }}
  .evidence-item .ev-value {{ color:#1e293b; font-variant-numeric:tabular-nums; }}
  .evidence-item .ev-value strong {{ color:var(--accent); }}
  .evidence-item.summary {{ background:#fef3c7; border-color:#fbbf24; }}
  .evidence-item.summary .ev-label {{ color:#b45309; font-weight:700; }}
  .evidence-item.summary .ev-value {{ color:#78350f; font-weight:600; }}
  /* mini table */
  .mini-table {{ width:100%; border-collapse:collapse; font-size:0.82rem; margin:4px 0; }}
  .mini-table th {{ background:#f8fafc; padding:8px 10px; text-align:left; font-weight:700; color:#475569; border-bottom:2px solid #e2e8f0; font-size:0.78rem; }}
  .mini-table td {{ padding:7px 10px; border-bottom:1px solid #f1f5f9; }}
  .mini-table td.num {{ text-align:right; font-variant-numeric:tabular-nums; color:#1e293b; font-weight:600; }}
  .footer {{ text-align:center; color:#94a3b8; font-size:0.75rem; margin-top:32px; padding:16px; border-top:1px solid #e2e8f0; }}
  @media (max-width:768px) {{
    .tldr-grid {{ grid-template-columns:1fr 1fr; }}
    .evidence-item {{ grid-template-columns:1fr; gap:4px; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 NHN 시장 분석 — 핵심 인사이트 리포트</h1>
    <div class="subtitle">
      KR · JP · US 3국 시장 + 웹보드 심층 · 2022 ~ 2026.1Q 기간 분석<br>
      각 인사이트를 클릭하면 <strong>해석 + 차트 + 근거 데이터</strong>가 펼쳐집니다 (20개 핵심)
    </div>
    <div class="meta">
      기준: dw_app_monthly · in_revenue_top100_unified_os=TRUE · iOS+Android 합산 · revenue_krw_100 (ST 100% 보정 + 연도별 환율)<br>
      전/후 비교: 전(22~24, 36개월 월평균) vs 후(25~26.1Q, 15개월 월평균)
    </div>
  </div>

  <div class="tldr-section">
    <div class="tldr-label-main">한 줄 요약 (TL;DR)</div>
    {tldr_cards}
  </div>

  {sections_html}

  <div class="footer">
    출처: Sensor Tower · AI_mobilegame DB · 퍼블 국적 분류: NEXON→KR, FUNFLY→중화권 강제<br>
    총 {len(INSIGHTS)}개 핵심 인사이트 · 신규 진입 분석은 별도 업데이트 예정
  </div>
</div>
</body>
</html>'''

with open(OUT, 'w', encoding='utf-8') as f: f.write(html)
print(f"[저장] {OUT}")
print(f"[크기] {os.path.getsize(OUT)/1024:.1f} KB")
