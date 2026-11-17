# SPDX-License-Identifier: GPL-3.0-only
from pathlib import Path
import argparse
import cv2
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(
    description="Build a timestamped contact sheet from a local input movie."
)
parser.add_argument("clip", type=Path)
parser.add_argument("--out-dir", type=Path, default=Path("build") / "inspection")
args = parser.parse_args()
clip = cv2.VideoCapture(str(args.clip))
if not clip.isOpened() or not clip.get(cv2.CAP_PROP_FPS):
    parser.error("Could not read the input clip.")
out = args.out_dir
out.mkdir(parents=True, exist_ok=True)
duration = clip.get(cv2.CAP_PROP_FRAME_COUNT) / clip.get(cv2.CAP_PROP_FPS)
times = [0, 1.5, 5, 12, 21, 34, 48, 60, 76, 91, 107, 122, 136, 149, min(161, duration - 0.2)]
sheet = Image.new("RGB", (5 * 320, 3 * 206), "#15191e")
draw = ImageDraw.Draw(sheet)
for i, t in enumerate(times):
    clip.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, frame = clip.read()
    if not ok:
        continue
    im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if i in [0, 3, 7, 10, 14]:
        im.save(out / ("source-%03d.jpg" % t), quality=97)
    x, y = (i % 5) * 320, (i // 5) * 206
    sheet.paste(im.resize((320, 180), Image.Resampling.LANCZOS), (x, y))
    draw.text((x + 7, y + 184), "%.1f s" % t, fill="white")
sheet.save(out / "source-contact.jpg", quality=90)
clip.release()
