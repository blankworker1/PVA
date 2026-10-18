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

CHAMFER, GAP = 0.09, 0.025               # PV-cell corners (share of a tile) and the gap between cells

def cell(x, y, s):
    """A monocrystalline cell: a square with its corners cut off, inset by half the gap."""
    g, c = GAP * s / 2, CHAMFER * s
    x0, y0, x1, y1 = x + g, y + g, x + s - g, y + s - g
    pts = [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]
    return "M" + " L".join(f"{a:.3f},{b:.3f}" for a, b in pts) + "Z"

def build(lang, pv=False):
    months = ("June", "giugno")[lang == "it"]
    ink = PAPER if pv else BLACK
    body = [f'<rect x="{X0}" y="{Y0}" width="{SIDE}" height="{SIDE}" fill="{BLACK if pv else PAPER}"/>']
    for i in range(7):
        for p in range(1, 10):
            data = None if (p, i) in FAILED else day_data(p, i)
            x, y, uid = X0 + (p - 1) * S, Y0 + (i + 1) * S, f"{lang}{p}_{i}"
            if pv:
                body.append(f'<clipPath id="cell{uid}"><path d="{cell(x, y, S)}"/></clipPath><g clip-path="url(#cell{uid})">')
            body.append(tile_svg(DAYS[i], data, x, y, S, uid))
            if pv:
                body.append('</g>')
    cx = X0 + SIDE / 2
    body.append(f'<text x="{cx:.2f}" y="{Y0 + S * .62:.2f}" text-anchor="middle" font-size="7" letter-spacing="1.4" fill="{ink}">SUNDIAL · La Meridiana</text>')
    body.append(f'<text x="{cx:.2f}" y="{Y0 + S * 8.55:.2f}" text-anchor="middle" font-size="4.2" letter-spacing="0.8" fill="{ink}">'
                f'Bosa · 18 – 24 {months} 2027</text>')
    cap = ("Mock-up of the canonical print · 9 panels (columns) × 7 days (rows) · invented data · rules v1 (draft)",
           "Bozza della stampa · 9 pannelli (colonne) × 7 giorni (righe) · dati inventati · regole v1 (bozza)")[lang == "it"]
    cap2 = ("Same sky for all nine: clouds on the 20th, overcast on the 22nd, a cloudy morning on the 23rd. Panel 6 did not wake on the 20th.",
            "Lo stesso cielo per tutti e nove: nuvole il 20, coperto il 22, mattina nuvolosa il 23. Il pannello 6 non si è acceso il 20.")[lang == "it"]
    body.append(f'<text x="{X0}" y="{Y0 + SIDE + 9:.2f}" font-size="3" fill="#6f6a60">{cap}</text>')
    body.append(f'<text x="{X0}" y="{Y0 + SIDE + 14:.2f}" font-size="3" fill="#6f6a60">{cap2}</text>')
    if pv:
        cap = cap.replace("of the canonical print", "of the wall version").replace("Bozza della stampa", "Bozza della versione a parete")
        cap3 = ("63 dials cut as solar cells, corners chamfered, on black: the reverse of a real panel.",
                "63 quadranti tagliati come celle solari, angoli smussati, su nero: il rovescio di un pannello vero.")[lang == "it"]
        body.append(f'<text x="{X0}" y="{Y0 + SIDE + 19:.2f}" font-size="3" fill="#6f6a60">{cap3}</text>')
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
