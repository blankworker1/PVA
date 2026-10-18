"""
PVA — the rules, version 1 (draft), as drawing code.
Draws day tiles as SVG from a day's data. Used here for an A4 sample sheet;
the same functions can later lay out the 9 × 9 canonical sheet and its separations.

All geometry is in tile units (tile side = 1).
"""
import math
from datetime import datetime, date, timezone
from zoneinfo import ZoneInfo

# ---------------- place ----------------
LAT, LNG = 40.2986, 8.4970          # Bosa
TZ = ZoneInfo("Europe/Rome")

# ---------------- inks (screen approximations; final values from the print shop) ----------------
PAPER, OCHRE, RED, BLUE, BLACK = "#F4EFE4", "#E8B33A", "#B5452F", "#2E5A78", "#1E1D1B"

def multiply(a, b):
    """Translucent ink b printed over a."""
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{x * y // 255:02X}" for x, y in zip(pa, pb))

# ---------------- the rules ----------------
DEG_PER_MIN = 180.0 / 903           # Bosa's solstice day (15 h 03 m) spans 180°
HEAT_FULL   = 40.0                  # °C rise since sunrise that reaches the ring's inner edge
VIS_BANDS   = [(1, 5, 1), (6, 10, 2), (11, None, 3)]   # visitors per hour -> dot size step (× dot_min)

G = dict(                           # proportions (tile units)
    cx=0.5, cy=0.70,                # arc centre on the axis
    Ri=0.30, Ro=0.38,               # sun ring
    Rd=0.44,                        # visitor dots
    axis=0.014,                     # axis / seal thickness
    heat=0.016,                     # heat line width
    dot_min=0.0235,                 # one visitor (≈ 2 mm on an 85 mm tile)
    outline=0.012,                  # failed-day outline
)

# ---------------- sun (after SunCalc, Agafonkin) ----------------
def sun_times(d: date):
    rad = math.pi / 180
    J1970, J2000 = 2440588, 2451545
    noon_local = datetime(d.year, d.month, d.day, 12, tzinfo=TZ)
    dd = noon_local.timestamp() / 86400 - 0.5 + J1970 - J2000
    lw, phi = -LNG * rad, LAT * rad
    n = round(dd - 0.0009 - lw / (2 * math.pi))
    ds = 0.0009 + lw / (2 * math.pi) + n
    M = rad * (357.5291 + 0.98560028 * ds)
    C = rad * (1.9148 * math.sin(M) + 0.02 * math.sin(2 * M) + 0.0003 * math.sin(3 * M))
    L = M + C + rad * 102.9372 + math.pi
    dec = math.asin(math.sin(L) * math.sin(rad * 23.4397))
    Jnoon = J2000 + ds + 0.0053 * math.sin(M) - 0.0069 * math.sin(2 * L)
    w = math.acos((math.sin(-0.833 * rad) - math.sin(phi) * math.sin(dec)) / (math.cos(phi) * math.cos(dec)))
    Jset = J2000 + 0.0009 + (w + lw) / (2 * math.pi) + n + 0.0053 * math.sin(M) - 0.0069 * math.sin(2 * L)
    to_ts = lambda j: (j + 0.5 - J1970) * 86400
    return to_ts(2 * Jnoon - Jset), to_ts(Jnoon), to_ts(Jset)     # rise, solar noon, set (epoch s)

def local(ts):
    return datetime.fromtimestamp(ts, TZ)

# ---------------- tile ----------------
def tile_svg(d: date, data, x0, y0, size, uid):
    """
    data = None for a failed day, otherwise:
      sun:      dict {section k: True/False (or 1/0; -1/missing = unknown)}, 15-minute solar sections from solar noon
      temps:    list of (ts, °C) panel readings
      visitors: dict {solar hour offset k: visitors in the hour ending there}
    """
    rise, noon, sset = sun_times(d)
    s = size
    cx, cy = x0 + G["cx"] * s, y0 + G["cy"] * s
    Ri, Ro, Rd = G["Ri"] * s, G["Ro"] * s, G["Rd"] * s

    def ang(ts):            # degrees from the top; morning negative
        return (ts - noon) / 60 * DEG_PER_MIN
    def pol(r, a):
        t = math.radians(a)
        return cx + r * math.sin(t), cy - r * math.cos(t)
    def band(a0, a1, r0, r1, steps=48):
        p = [pol(r1, a0 + (a1 - a0) * i / steps) for i in range(steps + 1)]
        p += [pol(r0, a1 - (a1 - a0) * i / steps) for i in range(steps + 1)]
        return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in p) + "Z"

    out = [f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{s:.2f}" height="{s:.2f}" fill="{PAPER}"/>']
    a_rise, a_set = ang(rise), ang(sset)
    axis = f'<rect x="{cx - Ro:.2f}" y="{cy:.2f}" width="{2 * Ro:.2f}" height="{G["axis"] * s:.2f}" fill="{BLACK}"/>'

    if data is None:        # failed day: bare bones, black only
        w = G["outline"] * s
        out.append(f'<path d="{band(a_rise, a_set, Ri, Ro)}" fill="none" stroke="{BLACK}" stroke-width="{w:.2f}" stroke-linejoin="miter"/>')
        out.append(axis)
        return "".join(out)

    # 1. sun ring: 15-minute sections in solar time, counted from solar noon.
    #    data["sun"][k] is True if most short-circuit readings in section k were above
    #    a third of the panel's clear-noon current. Section k runs noon+k·15 min to noon+(k+1)·15 min.
    #    Unknown sections (no reading, sensor not calibrated) are left as a thin black outline,
    #    as on the panel page. Neighbours of the same colour are merged.
    SEC = 15 * 60
    k_first = math.floor((rise - noon) / SEC)
    k_last = math.ceil((sset - noon) / SEC) - 1
    runs = []                                        # (t0, t1, colour)
    for k in range(k_first, k_last + 1):
        t0 = max(rise, noon + k * SEC)
        t1 = min(sset, noon + (k + 1) * SEC)
        v = data["sun"].get(k)
        col = OCHRE if v in (True, 1) else BLUE if v in (False, 0) else None
        if runs and runs[-1][2] == col:
            runs[-1] = (runs[-1][0], t1, col)
        else:
            runs.append((t0, t1, col))
    segs = [(band(ang(t0), ang(t1), Ri, Ro), col) for t0, t1, col in runs if col]
    for path, col in segs:
        out.append(f'<path d="{path}" fill="{col}"/>')
    for t0, t1, col in runs:
        if not col:
            out.append(f'<path d="{band(ang(t0), ang(t1), Ri, Ro)}" fill="none" stroke="{BLACK}" '
                       f'stroke-width="{G["outline"] * s / 2:.2f}"/>')

    # 2. heat: rise since the first reading, time projected onto the axis, no upper limit
    temps = [(t, c) for t, c in data["temps"] if rise <= t <= sset]
    if temps:
        base = temps[0][1]
        pts = []
        for t, c in temps:
            x = cx + Ri * math.sin(math.radians(ang(t)))
            y = cy - (c - base) / HEAT_FULL * Ri
            pts.append(f"{x:.2f},{y:.2f}")
        line = "M" + " L".join(pts)
        hw = G["heat"] * s
        out.append(f'<path d="{line}" fill="none" stroke="{RED}" stroke-width="{hw:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')
        # overprint: where the red crosses the ring, the inks mix
        for i, (path, col) in enumerate(segs):
            cid = f"c{uid}_{i}"
            out.append(f'<clipPath id="{cid}"><path d="{path}"/></clipPath>')
            out.append(f'<path d="{line}" fill="none" stroke="{multiply(col, RED)}" stroke-width="{hw:.2f}" '
                       f'stroke-linecap="round" stroke-linejoin="round" clip-path="url(#{cid})"/>')

    # 3. axis / sunset seal
    out.append(axis)

    # 4. presence: one dot per solar hour, three sizes by band (1–5, 6–10, 11+), none if nobody came
    for k, v in data["visitors"].items():
        a = k * 60 * DEG_PER_MIN
        if not v or not (a_rise <= a <= a_set):
            continue
        step = next(m for lo, hi, m in VIS_BANDS if v >= lo and (hi is None or v <= hi))
        dia = G["dot_min"] * s * step
        x, y = pol(Rd, a)
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{dia / 2:.2f}" fill="{BLACK}"/>')
    return "".join(out)
