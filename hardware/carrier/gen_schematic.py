#!/usr/bin/env python3
"""Generate the PVA carrier v1 KiCad 7 schematic from parts.py.

Label style: every pin gets a short wire stub and a net label, so the drawing
is exactly the netlist in parts.py. Run, then check with kicad-cli (see build.sh).
"""
import re, uuid, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from parts import SECTIONS, PWR_FLAGS

SYMDIR = "/usr/share/kicad/symbols"
_libcache = {}

def U(): return str(uuid.uuid4())

def lib_text(lib):
    if lib not in _libcache:
        _libcache[lib] = open(f"{SYMDIR}/{lib}.kicad_sym").read()
    return _libcache[lib]

def find_block(text, name):
    i = text.find(f'\n  (symbol "{name}"')
    if i < 0: raise KeyError(name)
    i += 1
    depth = 0
    for j in range(i, len(text)):
        c = text[j]
        if c == '(': depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0: return text[i:j + 1]
    raise ValueError(name)

def flat_symbol(lib, name):
    """Return the symbol block flattened (extends resolved), root named lib:name."""
    t = lib_text(lib)
    blk = find_block(t, name)
    m = re.search(r'\(extends "([^"]+)"\)', blk)
    if m:
        base = m.group(1)
        bblk = find_block(t, base)
        # keep derived properties, take base graphics/pins
        props = re.findall(r'\n    \(property "[^"]+" .*?\n    \)', blk, re.S)
        body = re.sub(r'\n    \(property "[^"]+" .*?\n    \)', '', bblk, flags=re.S)
        body = body.replace(f'(symbol "{base}_', f'(symbol "{name}_')
        head, rest = body.split('\n', 1)
        head = head.replace(f'(symbol "{base}"', f'(symbol "{name}"')
        blk = head + ''.join(props) + '\n' + rest
    blk = blk.replace(f'(symbol "{name}"', f'(symbol "{lib}:{name}"', 1)
    return blk

def pins_of(blk):
    out = {}
    for m in re.finditer(r'\(pin (\w+) \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\) \(length ([-\d.]+)\).*?\(name "([^"]*)".*?\(number "([^"]*)"', blk, re.S):
        out[m.group(7)] = (float(m.group(2)), float(m.group(3)), int(m.group(4)), m.group(1))
    return out

def bbox(pins):
    xs = [p[0] for p in pins.values()] or [0]; ys = [p[1] for p in pins.values()] or [0]
    return min(xs), max(xs), min(ys), max(ys)

def snap(v, g=2.54): return round(v / g) * g

ROOT = U()
lib_blocks = {}
items = []
STUB = 2.54

def ref_val(ref, value, x, y, pins, hide_ref):
    x0, x1, y0, y1 = bbox(pins)
    vertical = pins and all(p[2] in (90, 270) for p in pins.values())
    if vertical:   # text beside the part, clear of the vertical net labels
        tx = x + max(x1, 1.27) + 2.54
        return (f'    (property "Reference" "{ref}" (at {tx:.2f} {y - 1.27:.2f} 0) (effects (font (size 1.27 1.27)) (justify left){hide_ref}))\n'
                f'    (property "Value" "{value}" (at {tx:.2f} {y + 1.27:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))\n')
    mixed = pins and any(p[2] in (90, 270) for p in pins.values())
    if mixed:      # pins top/bottom and sides: put text at the right-hand corners, clear of labels
        tx = x + max(x1, 2.54) + 1.27
        return (f'    (property "Reference" "{ref}" (at {tx:.2f} {y - max(y1, 2.54) - 3.81:.2f} 0) (effects (font (size 1.27 1.27)) (justify left){hide_ref}))\n'
                f'    (property "Value" "{value}" (at {tx:.2f} {y - min(y0, -2.54) + 3.81:.2f} 0) (effects (font (size 1.27 1.27)) (justify left)))\n')
    return (f'    (property "Reference" "{ref}" (at {x:.2f} {y - max(y1, 2.54) - 3.81:.2f} 0) (effects (font (size 1.27 1.27)){hide_ref}))\n'
            f'    (property "Value" "{value}" (at {x:.2f} {y - min(y0, -2.54) + 3.81:.2f} 0) (effects (font (size 1.27 1.27))))\n')

def place(ref, lib, name, value, fp, netmap, x, y, in_bom=True, dnp=False, power=False):
    key = f"{lib}:{name}"
    if key not in lib_blocks:
        lib_blocks[key] = flat_symbol(lib, name)
    pins = pins_of(lib_blocks[key])
    x, y = snap(x), snap(y)
    pin_uuids = " ".join(f'(pin "{n}" (uuid {U()}))' for n in pins)
    x0, x1, y0, y1 = bbox(pins)
    hide_ref = " hide" if power else ""
    s = (f'  (symbol (lib_id "{key}") (at {x:.2f} {y:.2f} 0) (unit 1)\n'
         f'    (in_bom {"yes" if in_bom else "no"}) (on_board {"no" if power else "yes"}) (dnp {"yes" if dnp else "no"})\n'
         f'    (uuid {U()})\n'
         + ref_val(ref, value, x, y, pins, hide_ref) +
         f'    (property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
         f'    (property "Datasheet" "~" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) hide))\n'
         f'    {pin_uuids}\n'
         f'    (instances (project "carrier" (path "/{ROOT}" (reference "{ref}") (unit 1))))\n  )')
    items.append(s)
    for num, (px, py, ang, etype) in pins.items():
        ex, ey = x + px, y - py                       # pin connection point in sheet coords
        bx = {0: 1, 90: 0, 180: -1, 270: 0}[ang]       # direction towards the body
        by = {0: 0, 90: -1, 180: 0, 270: 1}[ang]
        sx, sy = ex - bx * STUB, ey - by * STUB
        net = netmap.get(num)
        if net is None:
            if etype not in ("no_connect",) and not power:
                items.append(f'  (no_connect (at {ex:.2f} {ey:.2f}) (uuid {U()}))')
            continue
        items.append(f'  (wire (pts (xy {ex:.2f} {ey:.2f}) (xy {sx:.2f} {sy:.2f})) (stroke (width 0) (type default)) (uuid {U()}))')
        la = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[(-bx, -by)]
        just = "right" if la in (180, 270) else "left"
        items.append(f'  (label "{net}" (at {sx:.2f} {sy:.2f} {la}) (fields_autoplaced)\n'
                     f'    (effects (font (size 1.27 1.27)) (justify {just} bottom)) (uuid {U()}))')
    return x0, x1, y0, y1

def text(t, x, y, size=2.54):
    items.append(f'  (text "{t}" (at {x:.2f} {y:.2f} 0) (effects (font (size {size} {size}) bold) (justify left bottom)) (uuid {U()}))')

# ---- layout: sections flow down columns; parts in a grid inside each section ----
COL_W, CELL_W, PER_ROW, TOP, Y_MAX = 200, 48, 4, 45, 560
col, y = 0, TOP
text("PVA carrier board v1 - schematic draft generated from hardware/CARRIER.md. Label style: nets join by name. Engineer review required before manufacture.", 20, 22, 3)
def part_h(lib, name):
    blk = lib_blocks.get(f"{lib}:{name}") or flat_symbol(lib, name)
    pins = pins_of(blk); x0, x1, y0, y1 = bbox(pins)
    return max(y1, 2.54), -min(y0, -2.54), max(x1 - x0, 5)
for title, parts in SECTIONS:
    rows = [parts[i:i + PER_ROW] for i in range(0, len(parts), PER_ROW)]
    if any(p[1][1] in ("Conn_01x15", "Micro_SD_Card_Det_Hirose_DM3AT") for p in parts):
        rows = [[p] for p in parts] if len(parts) <= 2 else rows
    heights = [max(sum(part_h(*p[1])[:2]) for p in r) + 22 for r in rows]
    sec_h = 14 + sum(heights)
    if y + sec_h > Y_MAX and y > TOP:
        col += 1; y = TOP
    x_base = 25 + col * COL_W
    text(title, x_base, y)
    y += 14
    for r, h in zip(rows, heights):
        for i, (ref, (lib, name), value, fp, nets, note) in enumerate(r):
            up, down, w = part_h(lib, name)
            wide = name in ("Conn_01x15", "Micro_SD_Card_Det_Hirose_DM3AT", "DS3231M")
            cx = x_base + 22 + i * CELL_W + (20 if wide else 0)
            dnp = value.startswith("DNP") or "NOT fitted" in value
            place(ref, lib, name, value, fp, nets, cx, y + up + 8, dnp=dnp)
        y += h
    y += 8

# power flags
fx, fy = 25 + (col + 1) * COL_W, TOP
text("Power flags (ERC)", fx - 10, fy)
for i, net in enumerate(PWR_FLAGS):
    place(f"#FLG0{i+1}", "power", "PWR_FLAG", "PWR_FLAG", "", {"1": net}, fx + 10, fy + 20 + i * 15, in_bom=False, power=True)

sch = ['(kicad_sch (version 20230121) (generator eeschema)', f'  (uuid {ROOT})', '  (paper "A1")',
       '  (title_block (title "PVA carrier board v1") (date "2026-10-20") (rev "draft-1") (company "photovoltaic-art / SUNDIAL")',
       '    (comment 1 "Generated from hardware/CARRIER.md by gen_schematic.py") (comment 2 "Draft: engineer review required before manufacture"))',
       '  (lib_symbols']
for k, b in lib_blocks.items():
    sch.append('    ' + b.replace('\n', '\n  '))
sch.append('  )')
sch += items
sch.append('  (sheet_instances (path "/" (page "1")))')
sch.append(')')
open(os.path.join(os.path.dirname(__file__), "carrier.kicad_sch"), "w").write("\n".join(sch) + "\n")
print("parts:", sum(len(p) for _, p in SECTIONS), "symbols in lib:", len(lib_blocks))
