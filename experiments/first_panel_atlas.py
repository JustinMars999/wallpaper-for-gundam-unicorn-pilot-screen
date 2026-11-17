# SPDX-License-Identifier: GPL-3.0-only
"""Archival wireframe instrument study shown before the final PFD was adopted."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1] / "build" / "studies"
ROOT.mkdir(parents=True, exist_ok=True)
FONTS = Path("C:/Windows/Fonts")
W, H = 4096, 800
offsets = [0, 1536, 2176, 2816, 3456]
widths = [1536, 640, 640, 640, 640]
atlas = Image.new("RGB", (W, H))
blue = (104, 143, 219)
cyan = (144, 192, 222)
muted = (70, 83, 125)
grid = (21, 28, 53)
violet = (133, 124, 180)
rose = (192, 117, 145)
soft = (42, 52, 84)
amber = (191, 148, 111)


def font(px, bold=False):
    return ImageFont.truetype(str(FONTS / ("consolab.ttf" if bold else "consola.ttf")), px)


def label(d, xy, s, sz=21, fill=muted, bold=False):
    d.text(xy, s, font=font(sz, bold), fill=fill, stroke_width=0)


def stroke(d, pts, fill=muted, width=2):
    d.line(pts, fill=fill, width=width, joint="curve")


def brackets(d, box, col=muted, k=22):
    x1, y1, x2, y2 = box
    for x, sx in [(x1, 1), (x2, -1)]:
        for y, sy in [(y1, 1), (y2, -1)]:
            stroke(d, [(x + sx * k, y), (x, y), (x, y + sy * k)], col, 2)


def frame(w):
    im = Image.new("RGB", (w, 720), (9, 11, 26))
    d = ImageDraw.Draw(im)
    for x in range(16, w, 48):
        d.line((x, 65, x, 656), fill=grid)
    for y in range(81, 657, 48):
        d.line((14, y, w - 14, y), fill=grid)
    for y in (62, 659):
        d.line((20, y, w - 20, y), fill=(65, 74, 105), width=2)
    brackets(d, (15, 12, w - 16, 708), soft, 17)
    return im, d


# Original schematic, drawn as mirrored armor plates with distinct joint centres and a single horn.
def mech(d, mid, top, s):
    def p(x, y):
        return (round(mid + x * s), round(top + y * s))

    def plate(coords, col=blue, fill=(16, 27, 57)):
        for sign in (-1, 1):
            pts = [p(sign * x, y) for x, y in coords]
            d.polygon(pts, fill=fill)
            stroke(d, pts + [pts[0]], col, max(1, round(s * 1.2)))

    def seam(coords, col=muted):
        for sign in (-1, 1):
            stroke(d, [p(sign * x, y) for x, y in coords], col, max(1, round(s)))

    plate([(0, 21), (9, 26), (14, 36), (11, 49), (5, 53), (0, 50)], cyan)
    plate([(0, 22), (2, 8), (3, -3), (4, 10), (3, 23)], cyan)
    seam([(2, 35), (10, 32), (12, 35)], cyan)
    seam([(2, 39), (7, 41), (11, 37)], violet)
    plate(
        [(0, 52), (14, 50), (23, 57), (34, 55), (42, 62), (35, 79), (18, 83), (11, 92), (0, 86)],
        blue,
    )
    plate([(19, 56), (37, 47), (51, 48), (64, 62), (62, 73), (46, 74), (37, 66)], cyan)
    seam([(31, 55), (47, 54), (59, 65)])
    seam([(7, 62), (31, 62), (27, 70), (12, 75)], cyan)
    plate([(44, 77), (58, 73), (62, 88), (56, 104), (44, 100), (42, 89)])
    plate([(46, 102), (57, 104), (60, 118), (56, 135), (45, 137), (42, 126)])
    seam([(48, 110), (53, 113), (51, 129)], cyan)
    plate([(46, 138), (54, 138), (57, 144), (53, 151), (45, 149), (42, 144)])
    plate([(0, 86), (12, 90), (20, 85), (20, 98), (14, 107), (0, 106)])
    seam([(0, 94), (14, 96), (18, 91)])
    seam([(0, 102), (11, 102), (16, 99)])
    plate(
        [(0, 108), (12, 109), (23, 102), (28, 110), (30, 124), (22, 133), (10, 124), (0, 129)], cyan
    )
    plate([(13, 129), (25, 131), (29, 142), (24, 160), (14, 163), (9, 152)])
    plate([(13, 164), (25, 160), (30, 169), (26, 178), (14, 181), (11, 174)], cyan)
    plate([(15, 182), (26, 179), (32, 197), (26, 220), (14, 220), (10, 211)])
    seam([(14, 189), (19, 194), (17, 215)], violet)
    seam([(23, 190), (27, 199), (24, 210)])
    plate([(14, 221), (26, 221), (29, 229), (34, 234), (31, 238), (12, 236), (8, 231)], cyan)
    for z in (47, 86, 108, 165, 220):
        d.ellipse((*p(-2, z - 2), *p(2, z + 2)), outline=soft, width=1)
    d.line((*p(0, 55), *p(0, 123)), fill=muted, width=1)


panels = []
im, d = frame(1536)
label(d, (36, 17), "RX-0  /  UNICORN", 30, cyan, True)
label(d, (1140, 24), "SYSTEM MONITOR", 21, violet)
brackets(d, (495, 101, 1041, 632), blue, 31)
for y in range(139, 609, 35):
    d.line((478, y, 488 if y % 2 else 495, y), fill=muted, width=2)
    d.line((1046, y, 1060, y), fill=muted, width=2)
for x in [516, 1018]:
    d.ellipse((x - 3, 359, x + 3, 365), fill=cyan)
mech(d, 768, 117, 2.06)
label(d, (56, 107), "FRAME LINK", 27, blue, True)
label(d, (58, 153), "LINEAR SEAT", 19, muted)
label(d, (58, 210), "L   MANIPULATOR", 19, violet)
label(d, (58, 259), "R   MANIPULATOR", 19, violet)
label(d, (58, 356), "ACTUATOR BUS", 21, blue)
for i, s in enumerate(["PRIMARY", "SECONDARY", "RETURN"]):
    y = 411 + i * 48
    label(d, (59, y), s, 16, muted)
    for n in range(11):
        d.rectangle(
            (201 + n * 11, y + 5, 207 + n * 11, y + 14), fill=(78, 103, 131) if n < 9 - i else soft
        )
label(d, (1110, 110), "MOTION TRACE", 23, blue, True)
label(d, (1112, 154), "AXIS    X / Y / Z", 16, muted)
for j in range(3):
    y = 249 + j * 96
    d.line((1110, y, 1480, y), fill=soft, width=2)
    pts = [
        (
            1111 + i * 3,
            y
            - 11 * math.sin(i * 0.12 + j) * math.exp(-(((i - 60) / 40) ** 2))
            - 6 * math.cos(i * 0.046 + 2 * j),
        )
        for i in range(119)
    ]
    stroke(d, pts, muted, 2)
label(d, (1110, 552), "PSYCHO-FRAME", 19, violet)
label(d, (44, 678), "MOBILE SUIT  /  RX-0", 18, muted)
label(d, (1163, 678), "LINK  //  NORMAL", 18, muted)
panels.append(im)

im, d = frame(640)
label(d, (26, 16), "NAV / ADI", 32, cyan, True)
label(d, (32, 91), "ORBITAL REFERENCE", 19, violet)
for rr in (75, 115, 144):
    d.ellipse((320 - rr, 340 - rr, 320 + rr, 340 + rr), outline=soft, width=2)
for i in range(48):
    ang = 2 * math.pi * i / 48
    ra = 144
    rb = 129 if i % 4 == 0 else 138
    stroke(
        d,
        [
            (320 + math.cos(ang) * ra, 340 + math.sin(ang) * ra),
            (320 + math.cos(ang) * rb, 340 + math.sin(ang) * rb),
        ],
        muted,
        2,
    )
for x, y, s in [(309, 156, "N"), (303, 505, "S"), (139, 326, "W"), (478, 326, "E")]:
    label(d, (x, y), s, 21, violet)
label(d, (35, 578), "ATTITUDE", 20, blue)
label(d, (35, 677), "INERTIAL NAV", 19, muted)
panels.append(im)
im, d = frame(640)
label(d, (27, 16), "LINEAR SEAT", 31, cyan, True)
for top, s in [(102, "PITCH"), (367, "ROLL")]:
    label(d, (34, top), s, 23, blue, True)
    brackets(d, (34, top + 65, 603, top + 208), muted, 11)
    for x in range(44, 601, 40):
        d.line((x, top + 132, x + 4, top + 132), fill=muted, width=2)
label(d, (34, 677), "CONTROL INPUT", 19, muted)
panels.append(im)
im, d = frame(640)
label(d, (27, 16), "PROPULSION", 31, cyan, True)
for cx, cy in [(181, 282), (461, 282)]:
    for rad in (76, 89):
        d.arc((cx - rad, cy - rad, cx + rad, cy + rad), 120, 423, fill=muted, width=3)
    for i in range(13):
        a = (120 + i * 25) * math.pi / 180
        stroke(
            d,
            [
                (cx + 90 * math.cos(a), cy + 90 * math.sin(a)),
                (cx + 79 * math.cos(a), cy + 79 * math.sin(a)),
            ],
            blue,
            2,
        )
label(d, (134, 392), "PORT", 22, violet)
label(d, (408, 392), "STBD", 22, violet)
label(d, (46, 501), "THRUST", 24, blue)
label(d, (45, 677), "MAIN DRIVE", 19, muted)
panels.append(im)
im, d = frame(640)
label(d, (27, 16), "SYS / BUS", 31, cyan, True)
label(d, (31, 102), "POWER DISTRIBUTION", 19, violet)
for row, name in enumerate(["ATTITUDE", "SENSORS", "SEAT", "FRAME", "DISPLAY", "COMMS"]):
    y = 172 + row * 64
    label(d, (41, y), name, 22, blue)
    for k in range(13):
        d.rectangle(
            (279 + k * 20, y + 5, 291 + k * 20, y + 20),
            fill=(62, 83, 126) if k < 10 + (row % 3) else soft,
        )
    d.rectangle((564, y + 5, 575, y + 17), outline=cyan, width=2)
label(d, (32, 677), "BUS A  /  NOMINAL", 18, muted)
panels.append(im)
for i, panel in enumerate(panels):
    atlas.paste(panel, (offsets[i], 0))
d = ImageDraw.Draw(atlas)
for i, ch in enumerate("0123456789"):
    d.text((i * 48 + 21, 759), ch, anchor="mm", font=font(52), fill=(175, 198, 235))
atlas.save(ROOT / "instruments.png")
