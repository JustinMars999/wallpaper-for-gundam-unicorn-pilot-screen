# SPDX-License-Identifier: GPL-3.0-only
"""Extract the optional canopy edge accent from a locally supplied reference clip."""

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def make_atlas(clip_path, start, end, historical_rgb=False):
    capture = cv2.VideoCapture(str(clip_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open {clip_path}")
    tile_width, tile_height = 576, 324
    dimensions = (8 * tile_height, 8 * tile_width)
    atlas = np.zeros((*dimensions, 3) if historical_rgb else dimensions, np.uint8)
    try:
        for index, second in enumerate(np.linspace(start, end, 64)):
            capture.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
            ok, image = capture.read()
            if not ok:
                raise ValueError(f"Could not read the frame at {second:.2f} seconds")
            tile = cv2.resize(image, (tile_width, tile_height), interpolation=cv2.INTER_AREA)
            blue, green, red = cv2.split(tile.astype(np.float32) / 255)
            blur = cv2.GaussianBlur(red, (0, 0), 2.8)
            edges = np.clip((red - blur) * 4.4, 0, 1)
            if historical_rgb:
                brightness = np.clip(blue * 0.5 + green * 0.34 + red * 0.16, 0, 1)
                tint = np.clip((red - green * 0.73 - blue * 0.17) * 2.6, 0, 1)
                edges = np.stack((edges, brightness, tint), axis=-1)
            sample = np.uint8(edges * 255 + 0.5)
            row, col = divmod(index, 8)
            y, x = row * tile_height, col * tile_width
            atlas[y : y + tile_height, x : x + tile_width] = sample
    finally:
        capture.release()
    return Image.fromarray(atlas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clip", type=Path)
    parser.add_argument("--output", type=Path, default=Path("build/canopy-edges.png"))
    parser.add_argument(
        "--historical-rgb",
        action="store_true",
        help="Also extract brightness and tint for the retired wireframe study.",
    )
    parser.add_argument("--start", type=float, default=13.0, help="First sample in seconds")
    parser.add_argument("--end", type=float, default=146.0, help="Last sample in seconds")
    args = parser.parse_args()
    if args.start < 0 or args.end <= args.start:
        parser.error("Choose a nonnegative start and a later end time.")
    image = make_atlas(args.clip, args.start, args.end, args.historical_rgb)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    print(f"Saved 64 samples to {args.output}")


if __name__ == "__main__":
    main()
