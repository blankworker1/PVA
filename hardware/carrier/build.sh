#!/bin/sh
# Regenerate the carrier schematic, netlist, PDF and BOM from parts.py (KiCad 7+ kicad-cli required)
set -e
cd "$(dirname "$0")"
python3 gen_schematic.py
kicad-cli sch export netlist -o carrier.net carrier.kicad_sch
python3 verify.py
kicad-cli sch export pdf -o carrier_schematic.pdf carrier.kicad_sch
python3 gen_bom.py
python3 checks.py > checks.txt
