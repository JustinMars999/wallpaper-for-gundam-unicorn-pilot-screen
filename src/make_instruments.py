# SPDX-License-Identifier: GPL-3.0-only
"""Raster typography and bezels for the five RX-0 multifunction displays."""
import argparse
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path("build") / "instruments.png")
parser.add_argument(
    "--font-dir",
    type=Path,
    default=Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
    help="Directory containing licensed Consolas regular and bold font files.",
)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)
from math import sin, cos, pi

F = args.font_dir
MINT = (150, 217, 190)
WHITE = (204, 222, 214)
DIM = (99, 140, 133)
LINE = (60, 84, 84)
GRID = (18, 33, 35)
DARK = (5, 12, 14)
AMBER = (229, 178, 104)
CYAN = (115, 191, 208)


def font(size, heavy=False):
    return ImageFont.truetype(str(F / ("consolab.ttf" if heavy else "consola.ttf")), size)


def txt(d, pos, s, sz=30, color=WHITE, anchor="la", heavy=False):
    d.text(pos, s, font=font(sz, heavy), fill=color, anchor=anchor, stroke_width=0)


def panel(width, top, code, keys, sel=0):
    im = Image.new("RGB", (width, 720), DARK)
    d = ImageDraw.Draw(im)
    d.rectangle((12, 13, width - 13, 75), fill=(13, 26, 27))
    txt(d, (29, 21), top, 42 if width > 640 else 38, WHITE, heavy=True)
    txt(d, (width - 30, 31), code, 26, MINT, "ra")
    d.line((18, 77, width - 18, 77), fill=LINE, width=3)
    d.line((18, 635, width - 18, 635), fill=LINE, width=3)
    for i, s in enumerate(keys):
        x0 = 20 + i * (width - 40) / len(keys)
        x1 = 20 + (i + 1) * (width - 40) / len(keys)
        mid = (x0 + x1) / 2
        if i == sel:
            d.rectangle((x0 + 6, 650, x1 - 6, 697), outline=MINT, width=2)
            d.rectangle((x0 + 7, 651, x1 - 7, 696), fill=(20, 42, 36))
        elif i:
            d.line((x0, 657, x0, 688), fill=LINE, width=2)
        txt(d, (mid, 673), s, 30 if width > 640 else 27, WHITE if i == sel else DIM, "mm", True)
    return im, d


panels = []
im, d = panel(1536, "RX-0  UNICORN", "PFD   01", ["PFD", "NAV", "ENG", "SYS", "COM"])
txt(d, (786, 36), "UNICORN MODE   /   NT-D STBY", 26, DIM, "ma")
txt(d, (54, 104), "VELOCITY", 34, MINT, heavy=True)
txt(d, (58, 150), "M/S", 24, DIM)
txt(d, (1480, 104), "ALTITUDE", 34, MINT, "ra", True)
txt(d, (1477, 150), "KM", 24, DIM, "ra")
txt(d, (767, 83), "HDG", 21, DIM, "ma")
d.rectangle((393, 175, 1143, 570), fill=(5, 12, 16), outline=LINE, width=3)
txt(d, (49, 571), "THR", 26, DIM)
txt(d, (53, 602), "% CMD", 18, DIM)
txt(d, (1199, 568), "V/S", 26, DIM)
txt(d, (1200, 600), "M/S", 19, DIM)
txt(d, (768, 607), "LVLH   /   ATTITUDE", 23, DIM, "mm")
panels.append(im)

im, d = panel(640, "NAV / FORM", "02", ["MAP", "FPL", "RNG"])
txt(d, (33, 96), "RELATIVE MOTION", 26, DIM)
txt(d, (32, 563), "RNG", 25, DIM)
txt(d, (32, 592), "5 KM", 31, WHITE, heavy=True)
txt(d, (606, 582), "D-LINK  02", 26, MINT, "ra")
panels.append(im)
im, d = panel(640, "FLT CTRL", "03", ["CTL", "TRM", "ACT"])
txt(d, (36, 98), "MANUAL", 34, MINT, heavy=True)
txt(d, (606, 105), "INPUT", 25, DIM, "ra")
d.rectangle((61, 162, 576, 438), outline=LINE, width=2)
for x in range(113, 575, 51):
    d.line((x, 162, x, 438), fill=GRID)
for y in range(190, 437, 28):
    d.line((61, y, 576, y), fill=GRID)
d.line((320, 163, 320, 438), fill=LINE, width=2)
d.line((62, 300, 575, 300), fill=LINE, width=2)
txt(d, (36, 495), "PITCH", 27, DIM)
txt(d, (357, 495), "BANK", 27, DIM)
panels.append(im)
im, d = panel(640, "PROPULSION", "04", ["ENG", "PWR", "TMP"])
txt(d, (36, 99), "MAIN DRIVE", 28, DIM)
for cx, name in [(177, "L"), (463, "R")]:
    cy = 294
    rx = 101
    ry = 111
    d.arc((cx - rx, cy - ry, cx + rx, cy + ry), 135, 405, fill=LINE, width=8)
    d.arc((cx - rx, cy - ry, cx + rx, cy + ry), 375, 405, fill=(146, 106, 57), width=8)
    for j in range(11):
        a = (135 + 27 * j) * pi / 180
        d.line(
            (cx + rx * cos(a), cy + ry * sin(a), cx + (rx - 13) * cos(a), cy + (ry - 14) * sin(a)),
            fill=DIM,
            width=3,
        )
    txt(d, (cx, 425), name + "   %", 32, MINT, "mm", True)
txt(d, (40, 524), "COOLANT", 24, DIM)
txt(d, (608, 525), "NOM", 33, MINT, "ra", True)
d.line((40, 582, 604, 582), fill=LINE, width=2)
panels.append(im)
im, d = panel(640, "SYSTEMS", "05", ["SYS", "BIT", "LOG"])
txt(d, (36, 99), "RX-0 STATUS", 30, DIM, heavy=True)
for y, s, flag in [
    (165, "PSYCHO-FRAME", "SYNC"),
    (251, "NT-D", "STBY"),
    (337, "MAIN BUS", "ON"),
    (423, "DATALINK", "LINK"),
    (509, "THERMAL", "NORM"),
]:
    d.line((34, y + 55, 606, y + 55), fill=GRID, width=3)
    d.rectangle((36, y + 10, 46, y + 33), fill=MINT)
    txt(d, (65, y + 2), s, 31, WHITE)
    txt(d, (600, y + 1), flag, 31, AMBER if s == "NT-D" else MINT, "ra", True)
panels.append(im)
atlas = Image.new("RGB", (4096, 800))
for start, img in zip([0, 1536, 2176, 2816, 3456], panels):
    atlas.paste(img, (start, 0))
d = ImageDraw.Draw(atlas)
for i, ch in enumerate("0123456789+-"):
    d.text((i * 48 + 24, 759), ch, font=font(63, True), fill=(255, 255, 255), anchor="mm")
atlas.save(args.output)
print(
    "Primary flight, formation navigation, flight controls, propulsion and systems display faces ready."
)
