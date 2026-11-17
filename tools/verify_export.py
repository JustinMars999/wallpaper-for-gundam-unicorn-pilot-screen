# SPDX-License-Identifier: GPL-3.0-only
import argparse, json, subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

parser = argparse.ArgumentParser(
    description="Check a silent three-minute 4K60 release and measure the loop cut."
)
parser.add_argument("video", type=Path)
parser.add_argument("--ffmpeg", default="ffmpeg")
parser.add_argument("--ffprobe", default="ffprobe")
parser.add_argument(
    "--preview", type=Path, help="Optional JPEG destination for an actual decoded frame."
)
args = parser.parse_args()
out, ff, fp = args.video, args.ffmpeg, args.ffprobe


def call(cmd):
    return subprocess.run(
        list(map(str, cmd)), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    ).stdout


data = json.loads(call([fp, "-v", "error", "-show_streams", "-show_format", "-of", "json", out]))
assert len(data["streams"]) == 1, "The delivered wallpaper must contain only a video stream"
s = data["streams"][0]
assert (s["codec_type"], s["codec_name"], s["width"], s["height"], s["pix_fmt"]) == (
    "video",
    "h264",
    3840,
    2160,
    "yuv420p",
)
assert (
    s["profile"],
    s["level"],
    s["color_range"],
    s["color_space"],
    s["color_transfer"],
    s["color_primaries"],
) == ("High", 52, "tv", "bt709", "bt709", "bt709")
assert (
    s["r_frame_rate"] == "60/1" and s["avg_frame_rate"] == "60/1" and int(s["nb_frames"]) == 10800
)
assert abs(float(data["format"]["duration"]) - 180) < 0.00001


def has_faststart(path):
    with path.open("rb") as movie:
        while header := movie.read(8):
            if len(header) < 8:
                return False
            size = int.from_bytes(header[:4], "big")
            header_size = 8
            if size == 1:
                size = int.from_bytes(movie.read(8), "big")
                header_size = 16
            if header[4:] == b"moov":
                return True
            if header[4:] == b"mdat" or size < header_size:
                return False
            movie.seek(size - header_size, 1)
        return False


assert has_faststart(out), "The MP4 index must precede the media payload"
packets = json.loads(
    call(
        [
            fp,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=pts,duration",
            "-of",
            "json",
            out,
        ]
    )
)["packets"]
times = np.sort(np.array([int(p["pts"]) for p in packets]))
assert (
    len(times) == 10800 and times[0] == 0 and np.all(np.diff(times) == np.diff(times)[0])
), "Frame timestamps are not uniformly spaced"


def frames(sec, n, gray=True):
    fmt = "gray" if gray else "rgb24"
    raw = call(
        [
            ff,
            "-v",
            "error",
            "-ss",
            f"{sec:.6f}",
            "-i",
            out,
            "-map",
            "0:v:0",
            "-an",
            "-frames:v",
            n,
            "-vf",
            "scale=960:540:flags=area",
            "-pix_fmt",
            fmt,
            "-f",
            "rawvideo",
            "pipe:1",
        ]
    )
    a = np.frombuffer(raw, np.uint8).reshape((-1, 540, 960) if gray else (-1, 540, 960, 3))
    assert len(a) == n, (sec, len(a), n)
    return a


first = frames(0, 18)
last = frames(179.7, 18)
gop = frames(1.85, 18)


def mae(a, b):
    return float(np.abs(a.astype(np.float32) - b.astype(np.float32)).mean())


def ssim(a, b):
    a, b = [x.astype(np.float32) for x in [a, b]]
    blur = lambda x: cv2.GaussianBlur(x, (11, 11), 1.5)
    x, y = blur(a), blur(b)
    va = blur(a * a) - x * x
    vb = blur(b * b) - y * y
    co = blur(a * b) - x * y
    return float(
        (
            ((2 * x * y + 6.5025) * (2 * co + 58.5225))
            / ((x * x + y * y + 6.5025) * (va + vb + 58.5225))
        ).mean()
    )


seam = mae(last[-1], first[0])
neighbor = [mae(x[i], x[i + 1]) for x in [last, first, gop] for i in range(len(x) - 1)]
similarity = ssim(last[-1], first[0])
assert seam <= max(1.25, 4 * float(np.median(neighbor))) and similarity > 0.992, (seam, similarity)
sample = frames(48, 1, False)[0]
if args.preview:
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(sample).save(args.preview, quality=94)
assert sample.std() > 18 and first[0].mean() > 18
print(
    json.dumps(
        {
            "streams": len(data["streams"]),
            "audio_streams": 0,
            "codec": s["codec_name"],
            "size": [s["width"], s["height"]],
            "fps": s["avg_frame_rate"],
            "frames": int(s["nb_frames"]),
            "seconds": float(data["format"]["duration"]),
            "bytes": out.stat().st_size,
            "boundary_luma_MAE": seam,
            "adjacent_luma_MAE_median": float(np.median(neighbor)),
            "boundary_SSIM": similarity,
            "uniform_frame_timestamps": True,
            "faststart": True,
        },
        indent=2,
    )
)
