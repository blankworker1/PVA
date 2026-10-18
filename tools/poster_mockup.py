"""A4 mock-up of the canonical print: 9 panels x 7 days = 63 tiles, rules v1, invented data.
Columns are panels 1-9, rows are the seven days; the top row carries the title, the bottom row the dates."""
import math, random, sys
from datetime import date, timedelta
import cairosvg
from pva_rules import tile_svg, sun_times, PAPER, BLACK

random.seed(2027)
DAYS = [date(2027, 6, 18) + timedelta(i) for i in range(7)]

# each panel's own window of direct sun, in solar hours from noon. A vertical south face
# sees the June sun only from about 8:00 to 16:00 solar time (-4 .. +4).
PANELS = {
    1: [(-4.0, 4.0)],                      # open piazza
    2: [(-1.4, 1.2)],                      # narrow street
    3: [(-4.0, 1.6)],                      # the castle takes the afternoon
    4: [(-0.6, 4.0)],                      # west lane
    5: [(-4.0, 4.0)],                      # sea front
    6: [(-2.6, -0.6), (0.4, 2.6)],         # courtyard, a tree at noon
    7: [(-3.2, -1.1), (1.5, 4.0)],         # under the castle
    8: [(-4.0, 3.0)],                      # by the river
    9: [(-3.0, 1.5)],                       # the alley that loses the sun by three
}
BUSY = {1: 1.0, 2: 0.6, 3: 0.8, 4: 0.7, 5: 1.6, 6: 0.5, 7: 0.9, 8: 1.1, 9: 0.7}
FAILED = {(6, 2)}                          # panel 6 did not wake on day 2

def clouds(i):
    """One sky for all nine panels: cloud spans in solar hours, per day."""
    if i == 2:                             # passing clouds
        return [(-2.2, -1.6), (-0.4, 0.3), (1.0, 1.4), (2.6, 3.4)]
    if i == 4:                             # overcast, a few breaks
        out, t = [], -7.5
        for a, b in [(-2.8, -2.2), (0.6, 1.1), (2.9, 3.3)]:
            out.append((t, a)); t = b
        return out + [(t, 7.5)]
    if i == 5:                             # cloudy morning
        return [(-7.5, -1.2)]
    return []

def inside(h, spans):
    return any(a <= h < b for a, b in spans)

def day_data(p, i):
    d = DAYS[i]
    rise, noon, sset = sun_times(d)
    lit, sky = PANELS[p], clouds(i)
    sun_at = lambda t: inside((t - noon) / 3600, lit) and not inside((t - noon) / 3600, sky)
    # sections: majority of 90 readings
    sun = {}
    for k in range(math.floor((rise - noon) / 900), math.ceil((sset - noon) / 900)):
        t0, t1 = max(rise, noon + k * 900), min(sset, noon + (k + 1) * 900)
        hits = sum(sun_at(t0 + (t1 - t0) * (j + .5) / 90) for j in range(90))
        sun[k] = hits > 45
    # heat: the panel warms in sun, cools towards the air
    temps, T, t = [], 21 + random.uniform(-1.5, 1.5), rise + 900
    while t <= sset:
        h = (t - noon) / 3600
        air = 22 + 7 * math.cos(math.pi * (h - 2.5) / 12) + (-3 if i == 4 else 0)
        gain = 1.25 if sun_at(t) else 0.0
        T += gain * 5 / 6 * (1 + random.uniform(-.15, .15)) - 0.045 * (T - air)
        temps.append((t, T)); t += 300
    # presence: visitors per solar hour, more in the evening, more at the weekend
    weekend = d.weekday() >= 5
    vis = {}
    for k in range(-7, 8):
        lam = BUSY[p] * (1.5 + 2.5 * math.exp(-((k - 3) / 3) ** 2)) * (1.5 if weekend else 1)
        n = sum(random.random() < lam / 12 for _ in range(12)) + (random.random() < lam / 8) * random.randint(0, 6)
        if n: vis[k] = n
    return dict(sun=sun, temps=temps, visitors=vis)

SIDE = 186                                 # poster side on the A4 page, mm
X0, Y0 = (210 - SIDE) / 2, 30
S = SIDE / 9

# The wall version, in real millimetres: each dial printed on an A4 sheet, trimmed to a 210 mm
# "cell" with its corners cut like silicon (30 mm cut edge), on a black board. Gaps as measured
# on the panels, slightly over-accentuated: 2 mm between columns (places), 4 mm between rows (days).
WALL = dict(cell=210.0, gap_x=2.0, gap_y=4.0, chamfer=30.0 / math.sqrt(2), dial=0.9, margin=20.0)

def cell_path(x, y, s, c):
    pts = [(x + c, y), (x + s - c, y), (x + s, y + c), (x + s, y + s - c), (x + s - c, y + s),
           (x + c, y + s), (x, y + s - c), (x, y + c)]
    return "M" + " L".join(f"{a:.3f},{b:.3f}" for a, b in pts) + "Z"

def wall_size():
    W = WALL
    w = 9 * W["cell"] + 8 * W["gap_x"] + 2 * W["margin"]
    h = 9 * W["cell"] + 8 * W["gap_y"] + 2 * W["margin"]
    return w, h

def build(lang, pv=False):
    months = ("June", "giugno")[lang == "it"]
    body = []
    if not pv:
        body.append(f'<rect x="{X0}" y="{Y0}" width="{SIDE}" height="{SIDE}" fill="{PAPER}"/>')
        for i in range(7):
            for p in range(1, 10):
                data = None if (p, i) in FAILED else day_data(p, i)
                body.append(tile_svg(DAYS[i], data, X0 + (p - 1) * S, Y0 + (i + 1) * S, S, f"{lang}{p}_{i}"))
        cx, ink, top, bot, sc = X0 + SIDE / 2, BLACK, Y0 + S * .62, Y0 + S * 8.55, 1
        box_w = box_h = SIDE
    else:
        W = WALL
        ww, wh = wall_size()
        sc = SIDE / max(ww, wh)                       # mm on the wall -> mm on the A4 page
        box_w, box_h = ww * sc, wh * sc
        ox = (210 - box_w) / 2
        body.append(f'<rect x="{ox:.3f}" y="{Y0}" width="{box_w:.3f}" height="{box_h:.3f}" fill="{BLACK}"/>')
        c, d = W["cell"] * sc, W["cell"] * W["dial"] * sc
        pos = lambda col, row: (ox + (W["margin"] + col * (W["cell"] + W["gap_x"])) * sc,
                                Y0 + (W["margin"] + row * (W["cell"] + W["gap_y"])) * sc)
        for i in range(7):
            for p in range(1, 10):
                data = None if (p, i) in FAILED else day_data(p, i)
                x, y = pos(p - 1, i + 1)
                body.append(f'<path d="{cell_path(x, y, c, W["chamfer"] * sc)}" fill="{PAPER}"/>')
                body.append(tile_svg(DAYS[i], data, x + (c - d) / 2, y + (c - d) / 2, d, f"{lang}{p}_{i}"))
        cx, ink = ox + box_w / 2, PAPER
        top = pos(0, 0)[1] + c * .62
        bot = pos(0, 8)[1] + c * .55
    body.append(f'<text x="{cx:.2f}" y="{top:.2f}" text-anchor="middle" font-size="7" letter-spacing="1.4" fill="{ink}">SUNDIAL · La Meridiana</text>')
    body.append(f'<text x="{cx:.2f}" y="{bot:.2f}" text-anchor="middle" font-size="4.2" letter-spacing="0.8" fill="{ink}">'
                f'Bosa · 18 – 24 {months} 2027</text>')
    Xc = (210 - box_w) / 2
    cap = ("Mock-up of the canonical print · 9 panels (columns) × 7 days (rows) · invented data · rules v1 (draft)",
           "Bozza della stampa · 9 pannelli (colonne) × 7 giorni (righe) · dati inventati · regole v1 (bozza)")[lang == "it"]
    if pv:
        cap = cap.replace("of the canonical print", "of the wall version").replace("Bozza della stampa", "Bozza della versione a parete")
    cap2 = ("Same sky for all nine: clouds on the 20th, overcast on the 22nd, a cloudy morning on the 23rd. Panel 6 did not wake on the 20th.",
            "Lo stesso cielo per tutti e nove: nuvole il 20, coperto il 22, mattina nuvolosa il 23. Il pannello 6 non si è acceso il 20.")[lang == "it"]
    body.append(f'<text x="{Xc}" y="{Y0 + box_h + 9:.2f}" font-size="3" fill="#6f6a60">{cap}</text>')
    body.append(f'<text x="{Xc}" y="{Y0 + box_h + 14:.2f}" font-size="3" fill="#6f6a60">{cap2}</text>')
    if pv:
        ww, wh = wall_size()
        cap3 = (f"63 A4 sheets cut to 210 mm cells, 30 mm corner cuts, on black: the reverse of a real panel. Gaps 2 mm (places), 4 mm (days). Wall size {ww/1000:.2f} × {wh/1000:.2f} m.",
                f"63 fogli A4 tagliati a celle di 210 mm, angoli smussati di 30 mm, su nero: il rovescio di un pannello vero. Fughe 2 mm (luoghi), 4 mm (giorni). Misura {ww/1000:.2f} × {wh/1000:.2f} m.".replace("1.", "1,"))[lang == "it"]
        body.append(f'<text x="{Xc}" y="{Y0 + box_h + 19:.2f}" font-size="2.6" fill="#6f6a60">{cap3}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" viewBox="0 0 210 297"
 font-family="Helvetica, Arial, sans-serif"><rect width="210" height="297" fill="#FFFFFF"/>{"".join(body)}</svg>'''
    name = "pva_poster_pv_mockup" if pv else "pva_poster_mockup"
    suffix = "" if lang == "en" else "." + lang
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=f"../texts/{name}{suffix}.pdf")
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"{name}{suffix}_preview.png", output_width=1600)

for pv in (False, True):
    for lang in (sys.argv[1:] or ["en", "it"]):
        random.seed(2027)                  # same invented data in every version
        build(lang, pv)
print("done")
