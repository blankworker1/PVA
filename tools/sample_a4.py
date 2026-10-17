"""A4 sample sheet: two days × two locations, invented data, rules v1 (draft)."""
import math
from datetime import date, datetime
import cairosvg
from pva_rules import tile_svg, sun_times, TZ, BLACK, OCHRE, BLUE, RED

def ts(d, hm):
    h, m = map(int, hm.split(":"))
    return datetime(d.year, d.month, d.day, h, m, tzinfo=TZ).timestamp()

def temps(d, wake, sleep, start_c, peak_rise, peak_at, end_rise):
    """Quick rise, slow fall, still warm at the end."""
    t0, t1, tp = ts(d, wake), ts(d, sleep), ts(d, peak_at)
    out = []
    n = int((t1 - t0) / 300)
    for i in range(n + 1):
        t = t0 + i * 300
        if t <= tp:
            f = math.sin(math.pi / 2 * (t - t0) / (tp - t0)) ** 1.6
            r = peak_rise * f
        else:
            f = (t - tp) / (t1 - tp)
            r = end_rise + (peak_rise - end_rise) * (0.5 + 0.5 * math.cos(math.pi * f ** 0.8))
        out.append((t, start_c + r))
    return out

def sections(d, lit):
    """Simulate the short-circuit verdicts: a section is sun if most of it was lit."""
    rise, noon, sset = sun_times(d)
    spans = [(ts(d, a), ts(d, b)) for a, b in lit]
    out = {}
    for k in range(math.floor((rise - noon) / 900), math.ceil((sset - noon) / 900)):
        t0, t1 = max(rise, noon + k * 900), min(sset, noon + (k + 1) * 900)
        samples = [t0 + (t1 - t0) * (i + 0.5) / 90 for i in range(90)]
        hits = sum(any(a <= t < b for a, b in spans) for t in samples)
        out[k] = hits > 45
    return out

def day(d, lit, wake, sleep, start_c, peak, peak_at, end, visitors):
    return dict(sun=sections(d, lit),
                temps=temps(d, wake, sleep, start_c, peak, peak_at, end),
                visitors=visitors)

JUNE, OCT = date(2026, 6, 21), date(2026, 10, 16)
tiles = [
    # row 1: summer solstice
    (JUNE, "Panel 3 · narrow street",
     day(JUNE, [("10:05", "12:40"), ("12:55", "15:30")], "06:10", "21:00", 22, 24, "15:10", 10,
         {-3: 1, -2: 0, -1: 2, 0: 1, 1: 3, 2: 1, 3: 0, 4: 2, 5: 1})),
    (JUNE, "Panel 9 · facing the sea",
     day(JUNE, [("06:15", "21:00")], "06:05", "21:00", 20, 46, "15:40", 14,
         {-6: 1, -5: 0, -4: 2, -3: 3, -2: 2, -1: 4, 0: 5, 1: 3, 2: 4, 3: 6, 4: 7, 5: 9, 6: 12, 7: 5})),
    # row 2: today
    (OCT, "Panel 3 · narrow street",
     day(OCT, [("09:40", "13:10"), ("13:40", "16:05")], "07:55", "18:40", 14, 16, "14:20", 5,
         {-3: 1, -1: 2, 0: 1, 1: 0, 2: 3, 3: 1})),
    (OCT, "Panel 9 · facing the sea",
     day(OCT, [("07:55", "11:30"), ("11:50", "18:46")], "07:50", "18:46", 15, 31, "14:40", 8,
         {-5: 1, -4: 2, -3: 4, -2: 3, -1: 5, 0: 2, 1: 4, 2: 6, 3: 14, 4: 9, 5: 6})),
]

TILE, GAP_X, GAP_Y = 85, 12, 24
X0 = (210 - 2 * TILE - GAP_X) / 2
Y0 = 38

body = []
for i, (d, where, data) in enumerate(tiles):
    col, row = i % 2, i // 2
    x, y = X0 + col * (TILE + GAP_X), Y0 + row * (TILE + GAP_Y)
    body.append(tile_svg(d, data, x, y, TILE, i))
    rise, noon, sset = sun_times(d)
    fmt = lambda t: datetime.fromtimestamp(t, TZ).strftime("%H:%M")
    body.append(f'<text x="{x:.2f}" y="{y + TILE + 6:.2f}" font-size="3.4" fill="{BLACK}">{where}</text>')
    body.append(f'<text x="{x:.2f}" y="{y + TILE + 10.5:.2f}" font-size="2.8" fill="#6f6a60">'
                f'{d.strftime("%-d %B %Y")} · sunrise {fmt(rise)} · solar noon {fmt(noon)} · sunset {fmt(sset)}</text>')

legend_y = Y0 + 2 * TILE + GAP_Y + 24
sw = lambda x, col: f'<rect x="{x}" y="{legend_y - 2.6}" width="3.2" height="3.2" fill="{col}"/>'
legend = [
    sw(X0, OCHRE), f'<text x="{X0 + 5}" y="{legend_y}" font-size="2.8" fill="{BLACK}">direct sun</text>',
    sw(X0 + 28, BLUE), f'<text x="{X0 + 33}" y="{legend_y}" font-size="2.8" fill="{BLACK}">shade</text>',
    sw(X0 + 50, RED), f'<text x="{X0 + 55}" y="{legend_y}" font-size="2.8" fill="{BLACK}">heat: rise since sunrise, +40 °C at the ring</text>',
    sw(X0 + 128, BLACK), f'<text x="{X0 + 133}" y="{legend_y}" font-size="2.8" fill="{BLACK}">presence per solar hour: 1–5 · 6–10 · 11+</text>',
    f'<text x="{X0}" y="{legend_y + 7}" font-size="2.6" fill="#6f6a60">Invented data for illustration. Arc angle = day length against Bosa\'s solstice day (180°). Solar noon at the top.</text>',
]

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297"
 font-family="Helvetica, Arial, sans-serif">
<rect width="210" height="297" fill="#FFFFFF"/>
<text x="{X0}" y="22" font-size="6" letter-spacing="0.6" fill="{BLACK}">PVA Bosa</text>
<text x="{X0}" y="28.5" font-size="3.2" fill="#6f6a60">Sample sheet · rules v1 (draft) · two days, two locations</text>
{"".join(body)}
{"".join(legend)}
</svg>'''

open("pva_sample_a4.svg", "w").write(svg)
cairosvg.svg2pdf(bytestring=svg.encode(), write_to="pva_sample_a4.pdf")
cairosvg.svg2png(bytestring=svg.encode(), write_to="pva_sample_a4_preview.png", output_width=1240)
print("done")
