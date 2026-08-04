#!/usr/bin/env python3
"""Render only the current printable-part ID table PNG."""
from pathlib import Path
from resvg_py import svg_to_bytes

root = Path(__file__).resolve().parent
source = (root / "part_id_table_v06.svg").read_text(encoding="utf-8")
# resvg-py on Windows rejects physical mm roots; normalize only in memory.
source = source.replace('width="420mm" height="297mm"', 'width="420" height="297"')
(root / "part_id_table_v06.png").write_bytes(svg_to_bytes(svg_string=source, width=3508))
print("Rendered part_id_table_v06.png only.")
