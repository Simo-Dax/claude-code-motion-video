"""Step 1 — read the reel folder: probe every file, contact sheets, word-level transcription.

Usage:  python3 directives/skills/72_video_editing/scripts/ingest.py <reel_dir> [--lang it]

Writes into <reel_dir>/_work/:
  probe.json          one entry per source (duration, size, rotation, HDR, audio, creation time)
  sheets/<key>.jpg    contact sheet with timestamps — Read these to SEE the clips
  words/<key>.json    whisper words [{id, w, t0, t1}] (seconds, source timeline)
  transcript.md       every take, words tagged with ids → used to mark cuts at GATE 1
"""
import os
import argparse
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import (AUDIO_EXT, IMAGE_EXT, VIDEO_EXT, WHISPER_MODEL, ffprobe,
                    key, load_json, run, save_json, work)

HDR_TRC = {"smpte2084", "arib-std-b67"}


def probe(reel, rel):
    info = ffprobe(Path(reel) / rel)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    entry = {
        "src": rel,
        "kind": "video" if v else "audio",
        "duration": round(float(info["format"].get("duration", 0)), 3),
        "has_audio": a is not None,
        "created": info["format"].get("tags", {}).get("creation_time", ""),
    }
    if v:
        rot = 0
        for sd in v.get("side_data_list", []):
            rot = int(sd.get("rotation", rot))
        w, h = v["width"], v["height"]
        if abs(rot) in (90, 270):
            w, h = h, w
        entry.update({
            "width": w, "height": h, "rotation": rot,
            "fps": v.get("avg_frame_rate", ""),
            "codec": v["codec_name"],
            "hdr": v.get("color_transfer", "") in HDR_TRC,
            "vertical": h > w,
        })
    return entry


def contact_sheet(reel, entry, out):
    """Frames every ~1.5s (max 24), labelled with their timestamp."""
    dur = entry["duration"]
    n = max(1, min(24, int(dur / 1.5)))
    times = [round(dur * (i + 0.5) / n, 2) for i in range(n)]
    font = ImageFont.truetype(os.environ.get("VIDEO_FONT", "/System/Library/Fonts/HelveticaNeue.ttc"), 22, index=int(os.environ.get("VIDEO_FONT_INDEX", "1")))
    thumbs = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            f = Path(tmp) / f"{i}.jpg"
            run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", str(Path(reel) / entry["src"]),
                 "-frames:v", "1", "-vf", "scale=240:-2", "-y", str(f)])
            if f.exists():
                im = Image.open(f).convert("RGB")
                d = ImageDraw.Draw(im)
                d.rectangle([0, 0, 86, 30], fill=(0, 0, 0))
                d.text((6, 3), f"{t:.1f}s", font=font, fill=(255, 255, 0))
                thumbs.append(im)
    if not thumbs:
        return
    cols = 6
    tw, th = thumbs[0].size
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
    for i, im in enumerate(thumbs):
        sheet.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=82)


def transcribe(reel, entry, wd, lang):
    k = key(entry["src"])
    wav = wd / "audio" / f"{k}.wav"
    wav.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-i", str(Path(reel) / entry["src"]), "-vn",
         "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-y", str(wav)])
    base = wd / "words" / f"{k}.whisper"
    base.parent.mkdir(parents=True, exist_ok=True)
    # -ml 1 -sow → one segment per word, with its own start/end
    run(["whisper-cli", "-m", WHISPER_MODEL, "-l", lang, "-ml", "1", "-sow",
         "-oj", "-of", str(base), "-np", str(wav)])
    raw = load_json(str(base) + ".json")["transcription"]
    words = []
    for seg in raw:
        w = seg["text"].strip()
        if not w:
            continue
        t0, t1 = seg["offsets"]["from"] / 1000, seg["offsets"]["to"] / 1000
        if words and not any(c.isalnum() for c in w):   # stray punctuation → glue to previous word
            words[-1]["w"] += w
            continue
        words.append({"id": len(words), "w": w, "t0": round(t0, 3), "t1": round(t1, 3)})
    save_json(wd / "words" / f"{k}.json", words)
    return words


def transcript_lines(words):
    """Group words in lines on pauses > 0.6s or sentence punctuation."""
    lines, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if nxt is None or nxt["t0"] - w["t1"] > 0.6 or w["w"][-1] in ".?!":
            lines.append(cur)
            cur = []
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--lang", default="it")
    a = ap.parse_args()
    reel = Path(a.reel)
    wd = work(reel)

    sources = []
    for sub, exts in (("clips", VIDEO_EXT), ("voiceover", AUDIO_EXT | VIDEO_EXT)):
        for f in sorted((reel / sub).glob("*")):
            if f.suffix.lower() in exts:
                sources.append(f"{sub}/{f.name}")
    overlays = [f"overlays/{f.name}" for f in sorted((reel / "overlays").glob("*"))
                if f.suffix.lower() in IMAGE_EXT]
    music = [f"music/{f.name}" for f in sorted((reel / "music").glob("*"))
             if f.suffix.lower() in AUDIO_EXT]
    if not sources:
        raise SystemExit("✗ nessun file in clips/ o voiceover/")

    entries = [probe(reel, s) for s in sources]
    entries.sort(key=lambda e: (e["src"].split("/")[0], e["created"], e["src"]))

    md = ["# Transcript — word id tra [ ] (per GATE 1 si marcano gli id da tagliare)\n"]
    for e in entries:
        tag = f"{e['duration']}s"
        if e["kind"] == "video":
            tag += f" · {e['width']}x{e['height']} · {'HDR' if e['hdr'] else 'SDR'}"
            tag += "" if e["vertical"] else " · ⚠️ ORIZZONTALE (crop 9:16)"
            contact_sheet(reel, e, wd / "sheets" / f"{key(e['src'])}.jpg")
        words = transcribe(reel, e, wd, a.lang) if e["has_audio"] else []
        e["words"] = len(words)
        md.append(f"\n## {e['src']}  ({tag})\n")
        if not words:
            md.append("_nessun parlato rilevato_\n")
        for line in transcript_lines(words):
            md.append(f"`{line[0]['t0']:6.2f}s` " + " ".join(f"[{w['id']}]{w['w']}" for w in line))
        print(f"✓ {e['src']}  {tag}  words={len(words)}")

    save_json(wd / "probe.json", {"sources": entries, "overlays": overlays, "music": music})
    (wd / "transcript.md").write_text("\n".join(md) + "\n")
    print(f"✓ probe/sheets/transcript → {wd}")
    if overlays:
        print(f"  overlays: {', '.join(overlays)}")


if __name__ == "__main__":
    main()
