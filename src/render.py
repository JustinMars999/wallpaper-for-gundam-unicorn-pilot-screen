# SPDX-License-Identifier: GPL-3.0-only
"""Offscreen GL compositor. Encode directly from a BT.709 NV12 framebuffer."""
import argparse
import ctypes as C
import math
from pathlib import Path
import queue
import subprocess
import threading
import time
import sys
import os
import tempfile
import numpy as np
from PIL import Image
from PyQt5.QtGui import QGuiApplication, QSurfaceFormat, QOpenGLContext, QOffscreenSurface

root = Path(__file__).resolve().parent
project = root.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--seat", type=Path, default=project / "artwork" / "linear-seat.png")
parser.add_argument("--ship", type=Path, default=project / "artwork" / "formation-carrier.png")
parser.add_argument("--vista", type=Path, default=project / "artwork" / "earth-orbit.png")
parser.add_argument("--instruments", type=Path, default=project / "assets" / "instruments.png")
parser.add_argument("--reticle", type=Path, default=project / "assets" / "reticle.png")
parser.add_argument(
    "--avionics-shader",
    type=Path,
    default=root / "shaders" / "avionics.frag",
    help="Display shader to insert into the cockpit compositor.",
)
edges = parser.add_mutually_exclusive_group()
edges.add_argument(
    "--menu-edges",
    type=Path,
    default=project / "assets" / "canopy-edges.png",
    help="Replace the packaged single-channel canopy outline atlas.",
)
edges.add_argument(
    "--no-menu-edges",
    action="store_const",
    const=None,
    dest="menu_edges",
    help="Use only the independently drawn HUD reticle.",
)
parser.add_argument(
    "--ffmpeg", default="ffmpeg", help="Name or path of an FFmpeg executable with h264_nvenc."
)
parser.add_argument("--width", type=int, default=3840)
parser.add_argument("--height", type=int, default=2160)
parser.add_argument("--fps", type=int, default=60)
parser.add_argument(
    "--preview", action="store_true", help="Export eight stills and measure the loop boundary."
)
parser.add_argument("--preview-dir", type=Path, default=Path("build") / "preview")
parser.add_argument(
    "--sample", type=int, default=0, metavar="FRAMES", help="Encode only the first N frames."
)
parser.add_argument(
    "--output",
    type=Path,
    default=Path("build") / "RX-0-Unicorn-Orbital-Formation-4K60-Silent-Loop.mp4",
)
args = parser.parse_args()
width, height, fps = args.width, args.height, args.fps
if width <= 0 or width % 4 or height <= 0 or height % 2 or fps <= 0:
    parser.error(
        "NV12 packing requires positive dimensions, width divisible by four, even height and a positive frame rate."
    )
total = fps * 180
if not 0 <= args.sample <= total:
    parser.error("--sample must be between zero and the number of frames in the loop.")
if args.preview:
    args.preview_dir.mkdir(parents=True, exist_ok=True)
else:
    if args.output.exists():
        parser.error("Output already exists: " + str(args.output))
    args.output.parent.mkdir(parents=True, exist_ok=True)
print(
    "Canopy detail:",
    str(args.menu_edges) if args.menu_edges else "authored reticle only",
    flush=True,
)
app = QGuiApplication(["RX-0 compositor"])
fmt = QSurfaceFormat()
fmt.setVersion(3, 3)
fmt.setProfile(QSurfaceFormat.CoreProfile)
ctx = QOpenGLContext()
ctx.setFormat(fmt)
if not ctx.create():
    raise RuntimeError("OpenGL device unavailable")
surface = QOffscreenSurface()
surface.setFormat(ctx.format())
surface.create()
if not ctx.makeCurrent(surface):
    raise RuntimeError("OpenGL surface unavailable")
U = C.c_uint
I = C.c_int
F = C.c_float
P = C.c_void_p
S = C.c_char_p


def gl(name, rt, *sig):
    addr = ctx.getProcAddress(name.encode())
    if not addr:
        raise RuntimeError(name)
    return C.WINFUNCTYPE(rt, *sig)(int(addr))


def generate(fn):
    v = U()
    fn(1, C.byref(v))
    return v.value


getString = gl("glGetString", S, U)
print("GPU", getString(0x1F01).decode(), flush=True)
shader = gl("glCreateShader", U, U)
source = gl("glShaderSource", None, U, I, C.POINTER(S), P)
compileShader = gl("glCompileShader", None, U)
sGet = gl("glGetShaderiv", None, U, U, C.POINTER(I))
sLog = gl("glGetShaderInfoLog", None, U, I, P, P)
makeProgram = gl("glCreateProgram", U)
attach = gl("glAttachShader", None, U, U)
link = gl("glLinkProgram", None, U)
pGet = gl("glGetProgramiv", None, U, U, C.POINTER(I))
pLog = gl("glGetProgramInfoLog", None, U, I, P, P)
use = gl("glUseProgram", None, U)
uLocation = gl("glGetUniformLocation", I, U, S)
uI = gl("glUniform1i", None, I, I)
uF = gl("glUniform1f", None, I, F)
u2 = gl("glUniform2f", None, I, F, F)


def program(fragment):
    prog = makeProgram()
    vertex = "#version 330 core\nvoid main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));gl_Position=vec4(p*2.-1.,0.,1.);}"
    for code, stage in [(vertex, 0x8B31), (fragment, 0x8B30)]:
        sh = shader(stage)
        buf = S(code.encode())
        source(sh, 1, C.byref(buf), None)
        compileShader(sh)
        status = I()
        sGet(sh, 0x8B81, C.byref(status))
        if not status.value:
            err = C.create_string_buffer(12000)
            sLog(sh, len(err), None, err)
            raise RuntimeError(err.value.decode(errors="replace"))
        attach(prog, sh)
    link(prog)
    status = I()
    pGet(prog, 0x8B82, C.byref(status))
    if not status.value:
        err = C.create_string_buffer(12000)
        pLog(prog, len(err), None, err)
        raise RuntimeError(err.value.decode(errors="replace"))
    return prog


shader_dir = root / "shaders"
composition = (shader_dir / "cockpit.frag").read_text(encoding="utf8")
composition = composition.replace(
    '#include "avionics.frag"', args.avionics_shader.read_text(encoding="utf8").rstrip("\n")
)
main = program(composition)
pack = program(
    """#version 330 core
out vec4 result; uniform sampler2D frameTex; uniform vec2 fullSize;
float lum(vec3 p){return dot(p,vec3(.2126,.7152,.0722));}
float y8(vec3 p){return (16.+219.*lum(p))/255.;}
vec2 chrom(vec3 p){float y=lum(p);return vec2(128./255.)+(224./255.)*.5*(p.br-vec2(y))/vec2(.9278,.7874);}
void main(){
  ivec2 o=ivec2(gl_FragCoord.xy);int x=4*o.x, h=int(fullSize.y);
  if(o.y<h){int y=h-1-o.y;
    result=vec4(y8(texelFetch(frameTex,ivec2(x,y),0).rgb),y8(texelFetch(frameTex,ivec2(x+1,y),0).rgb),
      y8(texelFetch(frameTex,ivec2(x+2,y),0).rgb),y8(texelFetch(frameTex,ivec2(x+3,y),0).rgb));}
  else{float cy=float(h-(o.y-h)*2-1)/fullSize.y;
    result=vec4(chrom(texture(frameTex,vec2((float(x)+1.)/fullSize.x,cy)).rgb),
                chrom(texture(frameTex,vec2((float(x)+3.)/fullSize.x,cy)).rgb));}
}"""
)
genTex = gl("glGenTextures", None, I, C.POINTER(U))
bind = gl("glBindTexture", None, U, U)
active = gl("glActiveTexture", None, U)
param = gl("glTexParameteri", None, U, U, I)
texImage = gl("glTexImage2D", None, U, I, I, I, I, I, U, U, P)
mip = gl("glGenerateMipmap", None, U)
gl("glPixelStorei", None, U, I)(0x0CF5, 1)
gl("glPixelStorei", None, U, I)(0x0D05, 1)
TEX = 0x0DE1
RGBA = 0x1908
RGB = 0x1907
UB = 0x1401
FRAME = 0x8D40


def setTex(w, h, channels, data, levels):
    tex = generate(genTex)
    bind(TEX, tex)
    param(TEX, 0x2802, 0x812F)
    param(TEX, 0x2803, 0x812F)
    param(TEX, 0x2800, 0x2601)
    param(TEX, 0x2801, 0x2703 if levels else 0x2601)
    typ = RGBA if channels == 4 else RGB
    texImage(
        TEX,
        0,
        0x8058 if channels == 4 else 0x8051,
        w,
        h,
        0,
        typ,
        UB,
        P(data.ctypes.data) if data is not None else None,
    )
    if levels:
        mip(TEX)
    return tex


use(main)
textures = []
for i, (name, path, alpha) in enumerate(
    [
        ("vistaTex", args.vista, False),
        ("seatTex", args.seat, True),
        ("shipTex", args.ship, True),
        ("panelTex", args.instruments, False),
        ("reticleTex", args.reticle, True),
        ("originalTex", args.menu_edges, False),
    ]
):
    img = (
        Image.new("RGB", (1, 1))
        if path is None
        else Image.open(path).convert("RGBA" if alpha else "RGB")
    )
    pixels = np.array(img)
    if alpha:
        pixels[:, :, :3] = (
            (pixels[:, :, :3].astype(np.uint16) * pixels[:, :, 3:].astype(np.uint16) + 127) // 255
        ).astype(np.uint8)
    active(0x84C0 + i)
    textures.append(setTex(*img.size, pixels.shape[2], pixels, True))
    uI(uLocation(main, name.encode()), i)
active(0x84C0 + 6)
genF = gl("glGenFramebuffers", None, I, C.POINTER(U))
bindF = gl("glBindFramebuffer", None, U, U)
attachTex = gl("glFramebufferTexture2D", None, U, U, U, U, I)
fCheck = gl("glCheckFramebufferStatus", U, U)


def framebuffer(w, h):
    tex = setTex(w, h, 4, None, False)
    fb = generate(genF)
    bindF(FRAME, fb)
    attachTex(FRAME, 0x8CE0, TEX, tex, 0)
    if fCheck(FRAME) != 0x8CD5:
        raise RuntimeError("Incomplete framebuffer")
    return tex, fb


frameTex, frameFB = framebuffer(width, height)
active(0x84C0 + 7)
nvTex, nvFB = framebuffer(width // 4, height * 3 // 2)
vao = generate(gl("glGenVertexArrays", None, I, C.POINTER(U)))
gl("glBindVertexArray", None, U)(vao)
gl("glDisable", None, U)(0x0BD0)
draw = gl("glDrawArrays", None, U, I, I)
vp = gl("glViewport", None, I, I, I, I)
read = gl("glReadPixels", None, I, I, I, I, U, U, P)
active(0x84C0 + 6)
bind(TEX, frameTex)
use(pack)
uI(uLocation(pack, b"frameTex"), 6)
u2(uLocation(pack, b"fullSize"), width, height)
use(main)
u2(uLocation(main, b"resolution"), width, height)
pu = uLocation(main, b"phase")


def scene(frame):
    bindF(FRAME, frameFB)
    vp(0, 0, width, height)
    use(main)
    uF(pu, math.tau * (frame % total) / total)
    draw(4, 0, 3)


def image(frame):
    scene(frame)
    data = np.empty((height, width, 4), np.uint8)
    read(0, 0, width, height, RGBA, UB, P(data.ctypes.data))
    return Image.fromarray(data[::-1].copy(), "RGBA").convert("RGB")


if args.preview:
    for sec in (0, 22, 48, 75, 96, 124, 148, 173):
        image(sec * fps).save(
            args.preview_dir / ("pilot-%03d.jpg" % sec), quality=94, subsampling=0
        )
    a = np.asarray(image(-1), dtype=float)
    b = np.asarray(image(0), dtype=float)
    c = np.asarray(image(1), dtype=float)
    print(
        "Raw mean pixel change, last-to-first and first-to-next",
        np.abs(a - b).mean(),
        np.abs(c - b).mean(),
        flush=True,
    )
    sys.exit(0)

frames = args.sample or total
target = args.output.resolve()
with tempfile.TemporaryDirectory(prefix="rx0-render-", dir=target.parent) as staging:
    staged = Path(staging) / "video.mp4"
    command = [
        args.ffmpeg,
        "-hide_banner",
        "-v",
        "warning",
        "-nostdin",
        "-n",
        "-f",
        "rawvideo",
        "-pixel_format",
        "nv12",
        "-video_size",
        f"{width}x{height}",
        "-framerate",
        str(fps),
        "-i",
        "pipe:0",
        "-map",
        "0:v:0",
        "-an",
        "-c:v",
        "h264_nvenc",
        "-preset",
        "p5",
        "-tune",
        "hq",
        "-rc",
        "vbr",
        "-cq",
        "18",
        "-b:v",
        "16M",
        "-maxrate",
        "32M",
        "-bufsize",
        "48M",
        "-spatial-aq",
        "1",
        "-aq-strength",
        "7",
        "-profile:v",
        "high",
        "-level:v",
        "5.2",
        "-g",
        str(2 * fps),
        "-bf",
        "2",
        "-color_range",
        "tv",
        "-colorspace",
        "bt709",
        "-color_trc",
        "bt709",
        "-color_primaries",
        "bt709",
        "-metadata",
        "title=RX-0 Unicorn | Orbital Formation",
        "-movflags",
        "+faststart",
        str(staged),
    ]
    buffers = queue.Queue()
    ready = queue.Queue()
    for i in range(3):
        buffers.put(np.empty((height * 3 // 2, width), np.uint8))
    enc = subprocess.Popen(command, stdin=subprocess.PIPE, bufsize=0)
    writer_errors = []

    def writer():
        try:
            while True:
                arr = ready.get()
                if arr is None:
                    break
                remaining = memoryview(arr).cast("B")
                while remaining:
                    n = enc.stdin.write(remaining)
                    if not n:
                        raise BrokenPipeError("FFmpeg stopped reading video frames")
                    remaining = remaining[n:]
                buffers.put(arr)
        except Exception as exc:
            writer_errors.append(exc)
            buffers.put(None)
        finally:
            enc.stdin.close()

    thread = threading.Thread(target=writer, daemon=True)
    thread.start()
    start = time.perf_counter()
    try:
        for i in range(frames):
            scene(i)
            bindF(FRAME, nvFB)
            vp(0, 0, width // 4, height * 3 // 2)
            use(pack)
            draw(4, 0, 3)
            if writer_errors:
                raise writer_errors[0]
            buf = buffers.get()
            if buf is None:
                raise RuntimeError("Encoder stopped")
            read(0, 0, width // 4, height * 3 // 2, RGBA, UB, P(buf.ctypes.data))
            ready.put(buf)
            if (i + 1) % (fps * 10) == 0:
                msg = f"{i+1}/{frames} frames, {(i+1)/(time.perf_counter()-start):.1f} frames/s"
                print(msg, flush=True)
        ready.put(None)
        thread.join()
        if writer_errors:
            raise writer_errors[0]
        if enc.wait():
            raise RuntimeError("Encoding failed")
    except BaseException:
        if enc.poll() is None:
            enc.terminate()
        ready.put(None)
        thread.join()
        enc.wait()
        raise
    if os.name == "nt":
        os.rename(staged, target)
    else:
        os.link(staged, target)
    print(f"Completed {frames} frames in {time.perf_counter()-start:.1f}s: {target}", flush=True)
