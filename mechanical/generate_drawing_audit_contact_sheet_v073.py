#!/usr/bin/env python3
"""Generate a visual audit contact sheet for catalog drawing cards."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / "catalog" / "drawings.json").read_text("utf-8"))
OUTPUT = ROOT / "docs" / "drawing_audit_contact_sheet_v073.png"

entries = [item for item in CATALOG["drawings"] if item["id"] != "125"]
columns = 4
thumb_w, thumb_h = 420, 290
caption_h = 88
margin = 18
rows = (len(entries) + columns - 1) // columns
canvas_w = margin + columns * (thumb_w + margin)
canvas_h = 92 + margin + rows * (thumb_h + caption_h + margin)
canvas = Image.new("RGB", (canvas_w, canvas_h), "#d9dee1")
draw = ImageDraw.Draw(canvas)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a Cyrillic-capable font on Linux or Windows."""
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        Path("C:/Windows/Fonts") / ("arialbd.ttf" if bold else "arial.ttf"),
        Path("C:/Windows/Fonts") / ("seguisb.ttf" if bold else "segoeui.ttf"),
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(str(candidate), size)
        except OSError:
            continue
    return ImageFont.load_default()


title_font = load_font(34, bold=True)
font = load_font(17)
small = load_font(14)

draw.text((margin, 18), "Crucian v0.7.3 — визуальный аудит чертежей", fill="#172126", font=title_font)
draw.text((margin, 58), "Зелёный — current; серый — historical; синий — reference. Изготовление только по current-карточкам.", fill="#42545d", font=font)

status_color = {"current": "#2f8f63", "historical": "#68757b", "reference": "#3179a6"}
for index, item in enumerate(entries):
    row, col = divmod(index, columns)
    ox = margin + col * (thumb_w + margin)
    oy = 92 + margin + row * (thumb_h + caption_h + margin)
    card = Image.new("RGB", (thumb_w, thumb_h), "white")
    preview = ROOT / item["preview"]
    try:
        image = Image.open(preview).convert("RGB")
        image.thumbnail((thumb_w - 12, thumb_h - 12))
        card.paste(image, ((thumb_w - image.width) // 2, (thumb_h - image.height) // 2))
    except Exception as exc:
        cd = ImageDraw.Draw(card)
        cd.text((12, 12), f"Не удалось открыть:\n{item['preview']}\n{exc}", fill="#8c2f2f", font=small)
    canvas.paste(card, (ox, oy))
    color = status_color[item["status"]]
    draw.rectangle((ox, oy + thumb_h, ox + thumb_w, oy + thumb_h + 6), fill=color)
    draw.text((ox + 6, oy + thumb_h + 12), f"{item['id']} · {item['status']} · {item['version']}", fill=color, font=font)
    # Wrap the title into two concise lines.
    words = item["title"].split()
    lines, line = [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if len(candidate) > 43 and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    for offset, line in enumerate(lines[:2]):
        draw.text((ox + 6, oy + thumb_h + 38 + offset * 20), line, fill="#172126", font=small)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUTPUT, optimize=True)
print(f"Generated {OUTPUT.relative_to(ROOT)} ({len(entries)} drawings)")
