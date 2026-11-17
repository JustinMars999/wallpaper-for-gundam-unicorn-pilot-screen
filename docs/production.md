# Making Orbital Formation

The shot stays at the pilot’s eye level for three minutes. The carrier slides past the front of the RX-0, the pilot shifts pressure on the grips, and the attitude display follows the bank. An unbroken shot and a silent track layout let the sequence repeat on a desktop.

## From menu screen to pilot’s seat

The starting clip was Redz Schneider’s menu wallpaper. The supplied copy ran for 162.771882 seconds at 1920 × 1080 and 24000/1001 fps. Its H.264 video averaged 625,469 bits/s, with a stereo 44.1 kHz AAC track. A fifteen-frame contact sheet showed the dark menu design through most of the clip and fades at the ends. The second YouTube reference, from DT Entertainment, supplied the visual reference for the violet and rose panoramic HUD. [Credits and original links](../CREDITS.md)

The first experiment cleaned up the menu with light temporal denoising, debanding, spline scaling and restrained sharpening. It retained the camera position and original duration. The next design placed the viewer in the linear seat. Movie stills showed what makes the view recognisable: white gloves on separate side grips, knees in the foreground, a single central monitor stalk, four side displays and a clear panoramic view. A white ship seen behind the pilot in one still became the formation carrier.

The first cockpit study used a blue wireframe suit on the main display. The final review called for a believable aircraft-style instrument panel. The new design uses a moving attitude indicator as its centrepiece and reserves amber for the aircraft reference symbol, gauge needles and standby indications. The blue study’s complete panel generator and shader are in the [experiments directory](../experiments/).

## What goes into one frame

| Input | Size | Role |
| --- | --- | --- |
| `artwork/earth-orbit.png` | 1860 × 845 RGB | Oversized horizon, cloud deck, atmosphere and stars |
| `artwork/formation-carrier.png` | 1672 × 941 RGBA | Transparent ship with its own scale, translation, roll and exhaust |
| `artwork/linear-seat.png` | 1672 × 941 RGBA | Cockpit structure, pilot’s hands and knees, and monitor bezels |
| `assets/instruments.png` | 4096 × 800 RGB | Static face markings and glyphs for dynamic instrument readings |
| `assets/reticle.png` | 3200 × 1800 RGBA | Original HUD drawing on a transparent two-times working canvas |
| `assets/canopy-edges.png` | 4608 × 2592 grayscale | The single channel sampled for the faint menu-derived canopy accent |

ImageGen produced the three illustration layers. Their original pixel dimensions are listed above. OpenGL composites at the final 3840 × 2160 resolution and draws the moving instrument geometry there. The tagged checkout includes the selected PNGs. The generation prompts, use of references and per-file hashes are recorded separately. [Exact art briefs](art-direction.md) · [Asset SHA-256 manifest](asset-checksums.txt)

### Five working displays

| Position | Display | What moves |
| --- | --- | --- |
| Far left | NAV / FORM | Relative-position symbol, heading ticks and a rotating sweep |
| Inner left | FLT CTRL | Stick position and signed pitch and bank |
| Centre | Primary flight display | Artificial horizon, bank pointer, pitch ladder, heading strip, velocity and altitude tapes, vertical speed and commanded thrust |
| Inner right | PROPULSION | Left and right drive needles and values, plus a segmented coolant indication |
| Far right | SYSTEMS | Psycho-frame synchronisation, NT-D standby, main bus, data link and thermal indications, with a slowly pulsing status lamp |

The compositor maps each display to the four corners of its painted glass. Static titles and keys live on five regions of one atlas. The main region is 1536 pixels wide, followed by four 640-pixel regions. Their horizontal origins are 0, 1536, 2176, 2816 and 3456 pixels. The first 720 rows hold the faces. The bottom strip contains the digits and plus/minus glyphs. The shader samples those glyphs for live numbers and draws the needles and horizon separately. It softens the edge where the simulated glass meets the bezel. The telemetry is animated for this fictional scene. [Panel generator](../src/make_instruments.py) · [Display shader](../src/shaders/avionics.frag)

### Camera, canopy and loop

The compositor draws the Earth first, followed by the carrier and four blue aft exhaust plumes, then the HUD and pilot foreground. Transparent layers use premultiplied alpha to keep dark fringes off the edges. The horizon rolls more than the pilot’s seat. Each glove has a small, local displacement. The right grip leads the bank slightly. The left tracks the thrust cycle. Low-amplitude breathing adds a 37-cycle movement over the three minutes.

Each frame uses `phase = 2π × (frame mod 10800) / 10800` at 60 fps. The variables use integer harmonics of this phase. The last encoded frame is 10,799 and the next step is frame zero. This preserves motion through the cut without an extra held frame, fade or reversed closing shot. [Compositing shader](../src/shaders/cockpit.frag)

For the faint canopy outline, 64 positions were sampled at equal intervals from 13 to 146 seconds in the menu clip. Each frame was resized to 576 × 324 and arranged on an 8 × 8 atlas. The extraction takes the positive difference between the red channel and a Gaussian-blurred red channel (sigma 2.8), amplifies it by 4.4 and clamps it. The original study also stored brightness and tint. The final shader reads only the outline. It blends adjacent samples, colours them muted rose and fades them in towards the outer edge with a maximum gain of 0.21. The included grayscale PNG preserves the exact red-channel values used in the finished shot. [Texture extraction code](../src/make_menu_edges.py) · [HUD drawing code](../src/make_reticle.py)

## Rendering and encoding

The release machine ran Python 3.11.5 on Windows, using PyQt5 5.15.10, Qt 5.15.2, NumPy 1.24.3, Pillow 10.2.0 and OpenCV 4.10.0. The GPU was an NVIDIA GeForce RTX 4070 Laptop GPU using driver 571.96. The FFmpeg build identified itself as `n6.0-18-g27205c0b47-20230503`.

A Qt offscreen OpenGL 3.3 core context draws a full-screen triangle. Textures have mipmaps and linear filtering. A second shader packs the framebuffer into limited-range Rec. 709 NV12. It calculates luma from the 0.2126, 0.7152 and 0.0722 RGB weights, encodes it into levels 16–235, and subsamples chroma over 2 × 2 pixels. A three-buffer queue sends the frames directly to FFmpeg. [Complete renderer and NV12 packing shader](../src/render.py)

| Encoding choice | Release value |
| --- | --- |
| Container and codec | Fast-start MP4, H.264 High Level 5.2, 8-bit 4:2:0 |
| Rate control | NVIDIA NVENC, P5, high-quality tuning, VBR, CQ 18 |
| Rate parameters | 16 Mb/s target, 32 Mb/s maximum, 48 Mb buffer, spatial adaptive quantisation at strength 7 |
| GOP | 120-frame interval, up to 2 B-frames |
| Colour tags | Limited range, BT.709 primaries, transfer and matrix |
| Measured video bitrate | 31,797,638 bits/s |
| Sound | The encoder maps one video stream and uses `-an` |
| Container layout | The `moov` index precedes the media payload |

### Build and inspect

Run the setup commands in the [README](../README.md). The examples below use PowerShell from the repository root. The first command renders the complete scene from the included assets. Each encode needs a new output filename. The renderer moves a completed file into place after FFmpeg succeeds.

```powershell
$python = '.\.venv\Scripts\python.exe'
& $python src/render.py
& $python src/render.py --preview --preview-dir build/stills
& $python src/render.py --width 960 --height 540 --sample 120 --output build/two-seconds.mp4
& $python src/render.py --no-menu-edges --preview --preview-dir build/drawn-hud
& $python src/render.py --help
```

Use `--ffmpeg` for a particular executable. `--seat`, `--ship`, `--vista`, `--instruments`, `--reticle`, `--menu-edges` and `--avionics-shader` accept replacement files. The composition is designed for 16:9. Width must be divisible by four and height must be even for the NV12 packing pass. The default build is local and reads the six image files listed above.

To regenerate the textures, use the following commands. The type in the cockpit and reticle comes from a local licensed installation of Consolas Regular and Bold (`consola.ttf` and `consolab.ttf`). Both drawing commands accept `--font-dir`. The optional third command requires a locally supplied copy of the first reference video that you have the right to use. The input copy used for this project had SHA-256 `361eb706d1c8855db64ba85197f2a28e163845d9b516c54a3d1eed7d784876b`.

```powershell
& $python src/make_instruments.py --output build/instruments.png
& $python src/make_reticle.py --output build/reticle.png
& $python src/make_menu_edges.py "your-menu-source.mp4" --output build/canopy-edges.png
& $python src/render.py --instruments build/instruments.png --reticle build/reticle.png --menu-edges build/canopy-edges.png --output build/from-generated-textures.mp4
```

### Earlier studies

To recreate the first wireframe instrument study with your own copy of the menu clip, generate the historical three-channel atlas and use the included first-generation display shader.

```powershell
& $python experiments/first_panel_atlas.py
& $python src/make_menu_edges.py "your-menu-source.mp4" --historical-rgb --output build/study-rgb.png
& $python src/render.py --instruments build/studies/instruments.png --avionics-shader experiments/first-panel.glsl --menu-edges build/study-rgb.png --preview --preview-dir build/studies/frames
```

The original menu-only upscale used this FFmpeg command. It retained the audio stream for that early comparison. The downloadable pilot-eye wallpaper uses the separate, silent renderer above.

```powershell
ffmpeg -n -i "your-menu-source.mp4" -map 0:v:0 -map 0:a:0 -vf "hqdn3d=0.75:0.60:1.8:1.4,gradfun=strength=0.78:radius=14,scale=3840:2160:flags=spline+accurate_rnd+full_chroma_int,unsharp=5:5:0.34:5:5:0,format=yuv420p" -c:v h264_nvenc -preset p5 -tune hq -rc vbr -cq 17 -b:v 0 -maxrate 55M -bufsize 95M -profile:v high -c:a copy -color_range tv -colorspace bt709 -color_trc bt709 -color_primaries bt709 -movflags +faststart -metadata "title=RX-0 | Original Menu Remaster" build/menu-study.mp4
```

For the original contact sheet, run `tools/inspect_clip.py your-menu-source.mp4`. To arrange four locally supplied stills in the comparison layout, pass the menu, cockpit, long-form HUD and output images in that order to `tools/compare_references.py`.

## Release verification

The approved MP4 is 715,587,025 bytes. It contains 10,800 uniformly spaced frames in 180.000 seconds and zero audio streams. A full render from the packaged textures on the production machine matched the approved file byte for byte. Rebuilds on other drivers or encoders can give a different bitstream. The published SHA-256 identifies the exact download. [Movie SHA-256](SHA256SUMS.txt)

The seam check compared the last and first decoded frames at 960 × 540 in grayscale. Their mean absolute luma difference was 0.63579 on a 0–255 scale. The median across nearby adjacent-frame samples, including a sample around a regular keyframe, was 0.33534. The last-to-first structural similarity was 0.99660. Chrome also displayed media timestamps 179.983333 then 0.000000 seconds, and continued playing through the next frames.

```powershell
& $python tools/verify_export.py build/RX-0-Unicorn-Orbital-Formation-4K60-Silent-Loop.mp4 --preview build/decoded-48s.jpg
Get-FileHash -Algorithm SHA256 build/RX-0-Unicorn-Orbital-Formation-4K60-Silent-Loop.mp4
```

The optional browser test needs Node.js, an installed Chrome with H.264 playback, and the pinned Playwright package. Use `CHROME_PATH` if Chrome is installed in a custom location.

```powershell
npm install
npm run check:loop -- build/RX-0-Unicorn-Orbital-Formation-4K60-Silent-Loop.mp4
```

Creative direction and approval by JustinMars999. AI assistance credited to OpenAI ChatGPT / Codex, **GPT-6.2 Astra**, with the three illustration layers generated by OpenAI ImageGen. [Credits and rights](../CREDITS.md)
