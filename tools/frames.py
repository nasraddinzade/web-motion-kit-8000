#!/usr/bin/env python3
"""Видео -> кадры WebP для прокрутки по кадрам на canvas.

Пишет кадры frame_0001.webp..., manifest.json (число кадров, размер, общий вес, кадр-постер)
и лист кадров sheet.jpg для просмотра глазами.

Пример: python frames.py hero.mp4 --out frames/desktop --width 1600 --fps 30 --quality 80
        python frames.py hero.mp4 --out frames/mobile --width 900 --fps 24 --quality 72
        python frames.py --selftest

Нужен ffmpeg в PATH (или переменная FFMPEG). Видео чужое, открывается только через ffmpeg.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")


def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg упал: {' '.join(args)}\n{r.stderr[-800:]}")
    return r


def extract(video, out, width, fps, quality):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("frame_*.webp"):
        old.unlink()
    run([FFMPEG, "-v", "error", "-y", "-i", str(video),
         "-vf", f"fps={fps},scale={width}:-2:flags=lanczos",
         "-c:v", "libwebp", "-quality", str(quality), "-compression_level", "6",
         str(out / "frame_%04d.webp")])
    frames = sorted(out.glob("frame_*.webp"))
    if not frames:
        raise SystemExit("кадров нет: проверь видео")
    total = sum(f.stat().st_size for f in frames)
    cols = 8
    step = max(1, len(frames) // 32)
    run([FFMPEG, "-v", "error", "-y", "-i", str(out / "frame_%04d.webp"),
         "-vf", f"select='not(mod(n\\,{step}))',scale=200:-2,tile={cols}x4",
         "-frames:v", "1", str(out / "sheet.jpg")])
    manifest = {
        "source": pathlib.Path(video).name,
        "frameCount": len(frames),
        "width": width,
        "fps": fps,
        "quality": quality,
        "pattern": "frame_%04d.webp",
        "posterFrame": 0,
        "totalBytes": total,
        "averageBytes": total // len(frames),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def selftest():
    if not shutil.which(FFMPEG):
        raise SystemExit("нет ffmpeg")
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        vid = d / "test.mp4"
        run([FFMPEG, "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30:duration=2",
             "-pix_fmt", "yuv420p", str(vid)])
        m = extract(vid, d / "out", 640, 15, 70)
        ok1 = m["frameCount"] == 30 and m["totalBytes"] > 0 and (d / "out" / "sheet.jpg").exists()
        print(f"2 с при 15 к/с: кадров {m['frameCount']}, вес {m['totalBytes']} байт -> {'ок' if ok1 else 'ОШИБКА'}")
        bad = d / "bad.mp4"
        bad.write_bytes(b"not a video")
        try:
            extract(bad, d / "bad_out", 640, 15, 70)
            ok2 = False
        except SystemExit:
            ok2 = True
        print(f"битое видео отклонено -> {'ок' if ok2 else 'ОШИБКА'}")
        sys.exit(0 if ok1 and ok2 else 1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video", nargs="?")
    p.add_argument("--out", default="frames")
    p.add_argument("--width", type=int, default=1600)
    p.add_argument("--fps", type=float, default=30)
    p.add_argument("--quality", type=int, default=80)
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        selftest()
    if not a.video:
        p.error("укажи видео или --selftest")
    m = extract(a.video, a.out, a.width, a.fps, a.quality)
    print(json.dumps(m, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
