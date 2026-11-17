# SPDX-License-Identifier: GPL-3.0-only
"""Draw the two-times supersampled panoramic reticle."""
import argparse
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=Path("build") / "reticle.png")
parser.add_argument(
    "--font-dir",
    type=Path,
    default=Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
    help="Directory containing licensed Consolas regular and bold font files.",
)
args = parser.parse_args()
args.output.parent.mkdir(parents=True, exist_ok=True)


def font(px, bold=False):
    return ImageFont.truetype(str(args.font_dir / ("consolab.ttf" if bold else "consola.ttf")), px)


S = 2
hud = Image.new("RGBA", (1600 * S, 900 * S), (0, 0, 0, 0))
d = ImageDraw.Draw(hud)
lav = (163, 159, 221, 150)
pink = (235, 139, 168, 163)
faint = (152, 146, 203, 66)
pale = (219, 211, 236, 163)


def line(coords, c, w=1):
    d.line(
        [(round(x * S), round(y * S)) for x, y in coords],
        fill=c,
        width=max(1, round(w * S)),
        joint="curve",
    )


def mirror(coords, c, w=1):
    line(coords, c, w)
    line([(1600 - x, y) for x, y in coords], c, w)


def tx(x, y, s, size, c):
    d.text((int(x * S), int(y * S)), s, font=font(round(size * S)), fill=c)


mirror([(50, 33), (132, 33), (197, 89), (262, 89)], faint, 1)
mirror([(138, 28), (204, 89), (247, 89)], lav, 1.2)
mirror(
    [(475, 51), (502, 108), (477, 139), (499, 165), (475, 200), (452, 245), (467, 262)], lav, 1.4
)
mirror([(507, 107), (487, 138), (501, 138)], pink, 3)
mirror([(493, 107), (472, 138), (485, 155)], lav, 1.8)
mirror([(0, 265), (257, 265), (288, 284), (420, 284), (446, 306)], pink, 1.2)
mirror([(0, 278), (243, 278), (275, 299), (331, 299)], faint, 1)
mirror([(0, 348), (111, 348), (134, 328), (343, 328), (371, 346), (485, 346)], lav, 1.2)
mirror([(0, 356), (139, 356), (150, 345), (247, 345), (265, 359), (417, 359)], pink, 1.4)
mirror([(148, 379), (174, 379), (192, 361)], pink, 1.5)
mirror([(99, 390), (119, 390)], faint, 2)
mirror([(227, 92), (265, 92)], pink, 0.8)
line([(771, 180), (784, 192), (800, 192), (809, 200), (818, 192), (837, 192), (849, 181)], lav, 1.4)
line([(801, 188), (809, 196), (817, 188)], pink, 1.8)
line([(782, 301), (800, 316), (818, 301)], lav, 1.3)
line([(788, 298), (800, 308), (812, 298)], faint, 1)
tx(1034, 48, "NAV/ADI", 10, lav)
tx(1035, 235, "VSI", 9, faint)
tx(508, 228, "RX–ZERO", 9, lav)
tx(225, 96, "00", 8, lav)
tx(470, 284, "INERTIAL", 7, faint)
for x in (1062, 1092):
    for i in range(13):
        y = 74 + i * 11
        ln = 13 if i % 3 == 0 else 6
        line([(x, y), (x + ln, y)], lav if i % 3 == 0 else faint, 0.8)
for i in range(13):
    x = 697 + 16 * i
    ln = 8 if i % 3 == 0 else 4
    line([(x, 57), (x, 57 + ln)], faint, 0.8)
hud.save(args.output)
