"""Frame check for a rendered reel (skill 72_video_editing, references/qa.md).

Samples a frame every --step seconds, draws Instagram's UI zones on top
(top 220px, bottom 400px, right 130px button column) and tiles them into
contact sheets so overlaps and crops are visible at a glance. Also counts
visual changes (scene cuts) and, with --compare, does the same for a
reference video (e.g. best.mp4) so the pacing can be compared.

Usage:
  python3 directives/skills/72_video_editing/scripts/check_frames.py <project_dir> [video.mp4]
        [--step 0.25] [--compare best.mp4] [--scene 0.12] [--region top]

--region top counts changes in the top half only: in a split layout (references/formats.md, split screen) the graphic
changes there while the face keeps running, and the full-frame scene score misses most of them.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from common import H, W, ffprobe, run, work  # noqa: E402

ZONES = {"top": 220, "bottom": 400, "right": 130}
COLS, ROWS, TW = 8, 4, 180  # tile width 180 → 320 tall


def default_video(reel):
    out = Path(reel) / "_out"
    named = out / f"{Path(reel).name}.mp4"
    if named.exists():
        return named
    prev = out / "preview.mp4"
    if prev.exists():
        return prev
    sys.exit("✗ nessun video in _out/: passa il path del video")


def duration(path):
    return float(ffprobe(path)["format"]["duration"])


def scene_changes(path, thresh, region=None):
    """Timestamps where the picture (or its top half) changes by more than thresh (0-1)."""
    crop = "crop=iw:ih/2:0:0," if region == "top" else ""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-vf",
         f"{crop}select='gt(scene,{thresh})',showinfo", "-an", "-f", "null", "-"],
        capture_output=True, text=True)
    return [float(m) for m in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def zones_overlay(img):
    """Red tint on the zones IG covers, scaled to the tile."""
    s = img.width / W
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    tint = (255, 40, 40, 70)
    d.rectangle([0, 0, img.width, ZONES["top"] * s], fill=tint)
    d.rectangle([0, img.height - ZONES["bottom"] * s, img.width, img.height], fill=tint)
    d.rectangle([img.width - ZONES["right"] * s, 0, img.width, img.height], fill=tint)
    return Image.alpha_composite(img.convert("RGBA"), ov)


def sheets(path, step, dest):
    frames = dest / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    for f in frames.glob("*.jpg"):
        f.unlink()
    run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vf",
         f"fps={1 / step},scale={TW}:-2", str(frames / "f_%05d.jpg")])
    files = sorted(frames.glob("*.jpg"))
    per = COLS * ROWS
    th = int(TW * H / W)
    out = []
    for i in range(0, len(files), per):
        sheet = Image.new("RGB", (COLS * TW, ROWS * (th + 18)), "black")
        d = ImageDraw.Draw(sheet)
        for j, f in enumerate(files[i:i + per]):
            x, y = (j % COLS) * TW, (j // COLS) * (th + 18)
            tile = zones_overlay(Image.open(f).resize((TW, th)))
            sheet.paste(tile.convert("RGB"), (x, y + 18))
            d.text((x + 4, y + 3), f"{(i + j) * step:.2f}s", fill="white")
        p = dest / f"check_{i // per + 1:02d}.jpg"
        sheet.save(p, quality=85)
        out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--step", type=float, default=0.25)
    ap.add_argument("--compare")
    ap.add_argument("--scene", type=float, default=0.12)
    ap.add_argument("--region", choices=["top"])
    a = ap.parse_args()

    video = Path(a.video) if a.video else default_video(a.reel)
    dest = work(a.reel) / "check"
    for p in sheets(video, a.step, dest):
        print(f"  sheet  {p}")

    dur = duration(video)
    cuts = scene_changes(video, a.scene, a.region)
    first = f", primo a {cuts[0]:.1f}s" if cuts else ""
    print(f"✓ {video.name}: {dur:.1f}s, {len(cuts)} cambi visivi{' (metà alta)' if a.region else ''} "
          f"(uno ogni {dur / max(len(cuts), 1):.1f}s{first})")
    if a.compare:
        ref = Path(a.compare)
        rdur, rcuts = duration(ref), scene_changes(ref, a.scene, a.region)
        print(f"  {ref.name}: {rdur:.1f}s, {len(rcuts)} cambi visivi "
              f"(uno ogni {rdur / max(len(rcuts), 1):.1f}s{f', primo a {rcuts[0]:.1f}s' if rcuts else ''})")
        if len(cuts) / dur < len(rcuts) / rdur:
            print("  → ritmo più lento del riferimento: valuta beat in più")
        if cuts and rcuts and cuts[0] > rcuts[0]:
            print("  → primo cambio visivo più tardi del riferimento")
    gaps = [b - a_ for a_, b in zip([0] + cuts, cuts + [dur]) if b - a_ > 4]
    if gaps:
        print(f"  tratti statici > 4s: {len(gaps)} (il più lungo {max(gaps):.1f}s)")


if __name__ == "__main__":
    main()
