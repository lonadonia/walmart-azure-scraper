"""Render an asciinema v2 recording to an H.264 MP4 with no external recorder: pyte keeps the terminal's screen, Pillow
draws it, and ffmpeg encodes the frames. What is drawn is exactly what the recording holds. Idle time is capped.

usage: python render_cast.py INPUT.cast OUTPUT.mp4 [--fps 8] [--idle 2.0]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

import pyte
from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SIZE = 16
BG = (24, 26, 31)
FG = (225, 228, 232)
PALETTE = {
    "default": FG,
    "black": (70, 74, 80),
    "red": (240, 113, 120),
    "green": (152, 195, 121),
    "brown": (229, 192, 123),
    "yellow": (229, 192, 123),
    "blue": (97, 175, 239),
    "magenta": (198, 120, 221),
    "cyan": (86, 182, 194),
    "white": (225, 228, 232),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cast")
    ap.add_argument("mp4")
    ap.add_argument("--fps", type=int, default=8)
    ap.add_argument("--idle", type=float, default=2.0)
    a = ap.parse_args()

    with open(a.cast, encoding="utf-8") as f:
        head = json.loads(f.readline())
        events = [json.loads(line) for line in f if line.strip()]
    cols, rows = int(head["width"]), int(head["height"])
    font, bold = ImageFont.truetype(FONT, SIZE), ImageFont.truetype(BOLD, SIZE)
    cw = int(font.getlength("M"))
    ch = SIZE + 4
    width, height = (cols * cw + 16) // 2 * 2, (rows * ch + 16) // 2 * 2
    enc = subprocess.Popen(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}", "-r", str(a.fps), "-i", "-",
            "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", a.mp4,
        ],
        stdin=subprocess.PIPE,
    )  # fmt: skip
    assert enc.stdin is not None
    screen = pyte.Screen(cols, rows)
    stream = pyte.Stream(screen)

    def frame() -> bytes:
        img = Image.new("RGB", (width, height), BG)
        draw = ImageDraw.Draw(img)
        for y in range(rows):
            line = screen.buffer[y]
            for x in range(cols):
                c = line[x]
                if c.data == " " and c.bg == "default":
                    continue
                px, py = 8 + x * cw, 8 + y * ch
                if c.bg != "default":
                    draw.rectangle([px, py, px + cw, py + ch], fill=PALETTE.get(c.bg, BG))
                fill = PALETTE.get(c.fg, FG)
                draw.text((px, py), c.data, font=bold if c.bold else font, fill=fill)
        if not screen.cursor.hidden:
            px, py = 8 + screen.cursor.x * cw, 8 + screen.cursor.y * ch
            draw.rectangle([px, py + ch - 3, px + cw, py + ch - 1], fill=FG)
        return img.tobytes()

    step = 1.0 / a.fps
    clock = 0.0  # the video's time
    last = 0.0  # the recording's time of the last event
    next_frame = 0.0
    current = frame()
    frames = 0
    for at, kind, data in events:
        at = float(at)
        gap = min(at - last, a.idle)
        last = at
        target = clock + gap
        while next_frame <= target:
            enc.stdin.write(current)
            frames += 1
            next_frame += step
        clock = target
        if kind == "o":
            stream.feed(data)
            current = frame()
    for _ in range(a.fps * 3):
        enc.stdin.write(current)
        frames += 1
    enc.stdin.close()
    rc = enc.wait()
    print(json.dumps({"frames": frames, "seconds": round(frames / a.fps, 1), "size": [width, height], "ffmpeg_exit": rc}))
    return rc


if __name__ == "__main__":
    sys.exit(main())
