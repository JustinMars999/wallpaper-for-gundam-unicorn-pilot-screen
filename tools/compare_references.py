# SPDX-License-Identifier: GPL-3.0-only
"""Make the original four-up comparison from four locally supplied images."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "images",
    type=Path,
    nargs=4,
    metavar="IMAGE",
    help="Menu still, cockpit reference, HUD reference, decoded render.",
)
parser.add_argument("--output", type=Path, default=Path("build") / "reference-review.jpg")
args = parser.parse_args()
paths = args.images
names = [
    "Uploaded menu",
    "Movie cockpit reference",
    "Long-form HUD reference",
    "Completed RX-0 pilot view",
]
board = Image.new("RGB", (1152, 716), "#10191c")
pen = ImageDraw.Draw(board)
ft = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 17)
for i, (path, name) in enumerate(zip(paths, names)):
    im = Image.open(path).convert("RGB")
    im.thumbnail((568, 312), Image.Resampling.LANCZOS)
    x = (i % 2) * 576
    y = (i // 2) * 358
    board.paste(im, (x + (576 - im.width) // 2, y + (320 - im.height) // 2))
    pen.text((x + 13, y + 323), name, font=ft, fill="#d1dbdb")
args.output.parent.mkdir(parents=True, exist_ok=True)
board.save(args.output, quality=92)
