"""Final checks on a rendered reel (skill 72_video_editing, references/qa.md). Run them, don't claim them.

Usage:
  python3 directives/skills/72_video_editing/scripts/verify_final.py <project_dir> [video.mp4]
        [--max-pause 0.5] [--silence-db -35] [--lufs -14] [--no-words] [--lang it]

Checks, each printed with its measured value:
  format    H.264, 1080x1920 (540x960 for preview), 30fps, yuv420p, limited range (tv), AAC
  av        audio and video stream lengths within 0.05s
  lufs      integrated loudness within ±1 LU of the target
  pauses    no silence in the final audio longer than --max-pause (default: cuts.json max_pause, else 0.5)
  words     fresh whisper transcript of the video vs the words kept by the spine: missing / extra / doubled
  captions  caption text vs kept words (plan.py is known to drop short words)
  ending    the last 8s are whole: the last kept words are heard at the end
  pace      words per second (short-form reference 3.1-3.8)

Writes _work/check/verify.json. Exit 1 if a hard check fails (format, av, lufs, words < 90%).
"""
import argparse
import difflib
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import FPS, H, W, WHISPER_MODEL, ffprobe, key, load_json, run, save_json, work  # noqa: E402


def norm(w):
    return re.sub(r"[^\w']", "", w.lower())


def default_video(reel):
    out = reel / "_out"
    for p in (out / f"{reel.name}.mp4", out / "preview.mp4"):
        if p.exists():
            return p
    sys.exit("✗ nessun video in _out/: passa il path del video")


def kept_words(reel, edit):
    """Source words whose midpoint falls inside a spine segment, in spine order."""
    out, cache = [], {}
    for s in edit["spine"]:
        if s["src"] not in cache:
            cache[s["src"]] = load_json(reel / "_work" / "words" / f"{key(s['src'])}.json")
        out += [w["w"] for w in cache[s["src"]] if s["in"] <= (w["t0"] + w["t1"]) / 2 <= s["out"]]
    return out


def heard_words(video, cd, lang):
    wav = cd / "final.wav"
    run(["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", "-y", str(wav)])
    base = cd / "final.whisper"
    run(["whisper-cli", "-m", WHISPER_MODEL, "-l", lang, "-ml", "1", "-sow", "-oj", "-of", str(base),
         "-np", str(wav)])
    words = []
    for seg in load_json(str(base) + ".json")["transcription"]:
        w = seg["text"].strip()
        if w and any(c.isalnum() for c in w):
            words.append({"w": w, "t0": seg["offsets"]["from"] / 1000, "t1": seg["offsets"]["to"] / 1000})
    return words


def loudness(video):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vn",
                        "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else None


def silences(video, db, d):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vn",
                        "-af", f"silencedetect=n={db}dB:d={d}", "-f", "null", "-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    ends = re.findall(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", r.stderr)
    return [(max(s, 0), float(e), float(du)) for s, (e, du) in zip(starts, ends)]


def diff(expected, heard):
    a, b = [norm(w) for w in expected], [norm(w) for w in heard]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    missing, extra = [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace"):
            missing.append(" ".join(expected[i1:i2]))
        if op in ("insert", "replace"):
            extra.append(" ".join(heard[j1:j2]))
    return sm.ratio(), missing, extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--max-pause", type=float)
    ap.add_argument("--silence-db", type=float, default=-35)
    ap.add_argument("--lufs", type=float, default=-14)
    ap.add_argument("--no-words", action="store_true", help="skip whisper (fast re-check after a re-render)")
    ap.add_argument("--lang", default="it")
    a = ap.parse_args()

    reel = Path(a.reel).resolve()
    video = Path(a.video).resolve() if a.video else default_video(reel)
    edit = load_json(reel / "edit.json")
    cuts = reel / "_work" / "cuts.json"
    max_pause = a.max_pause or (load_json(cuts).get("max_pause") if cuts.exists() else None) or 0.5
    cd = work(reel) / "check"
    cd.mkdir(parents=True, exist_ok=True)
    rep, hard = {"video": str(video)}, []

    def line(ok, name, msg, is_hard=False):
        print(f"{'✓' if ok else '✗'} {name:<9}{msg}")
        rep[name] = {"ok": ok, "msg": msg}
        if not ok and is_hard:
            hard.append(name)

    info = ffprobe(video)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    preview = v["width"] == W // 2
    size = (W // 2, H // 2) if preview else (W, H)
    fps = float(Fraction(v.get("avg_frame_rate") or "0/1"))  # "30/1" → 30.0
    probs = [p for p, bad in [
        (f"{v['width']}x{v['height']} (atteso {size[0]}x{size[1]})", (v["width"], v["height"]) != size),
        (f"codec {v['codec_name']}", v["codec_name"] != "h264"),
        (f"{fps:.2f}fps", abs(fps - FPS) > 0.01),
        (f"pix_fmt {v.get('pix_fmt')}", v.get("pix_fmt") != "yuv420p"),
        (f"range {v.get('color_range', '?')} (serve tv: pc su IG = colori slavati)", v.get("color_range") != "tv"),
        ("audio mancante" if not au else f"audio {au['codec_name']}", not au or au["codec_name"] != "aac"),
    ] if bad]
    line(not probs, "format", "; ".join(probs) or
         f"h264 {size[0]}x{size[1]} 30fps yuv420p tv · aac{' (preview)' if preview else ''}", True)

    vd = float(v.get("duration", info["format"]["duration"]))
    ad = float(au.get("duration", vd)) if au else 0
    line(abs(vd - ad) <= 0.05, "av", f"video {vd:.3f}s · audio {ad:.3f}s · Δ {abs(vd - ad):.3f}s", True)

    lu = loudness(video)
    line(lu is not None and abs(lu - a.lufs) <= 1, "lufs", f"{lu} LUFS (target {a.lufs})", True)

    long_ = [s for s in silences(video, a.silence_db, max_pause)
             if s[1] < vd - 0.3 and s[0] > 0.05]          # lead-in and tail have their own rules
    line(not long_, "pauses", f"nessun silenzio > {max_pause}s a {a.silence_db:.0f}dB" if not long_ else
         f"{len(long_)} silenzi > {max_pause}s: " + ", ".join(f"{s:.2f}-{e:.2f} ({d:.2f}s)" for s, e, d in long_[:8]))

    kept = kept_words(reel, edit)
    caps = " ".join(c["text"] for c in edit["captions"]).split()
    r, miss, _ = diff(kept, caps)
    line(not miss, "captions", "caption = parole tenute" if not miss else
         f"{len(miss)} pezzi mancanti nelle caption ({r:.0%}): " + " | ".join(miss[:8]))

    if not a.no_words:
        heard = heard_words(video, cd, a.lang)
        hw = [w["w"] for w in heard]
        r, miss, extra = diff(kept, hw)
        doubled = [f"{w['w']} @{w['t0']:.1f}s" for p, w in zip(heard, heard[1:]) if norm(p["w"]) == norm(w["w"])]
        line(r >= 0.9, "words", f"{r:.0%} uguali · mancanti {miss[:6]} · in più {extra[:6]}"
             + (f" · doppie {doubled[:6]}" if doubled else ""), True)
        tail = [norm(w) for w in kept[-5:]]
        end_heard = [norm(w["w"]) for w in heard if w["t0"] >= vd - 8]
        whole = bool(tail) and " ".join(tail) in " ".join(end_heard)
        line(whole, "ending", "ultime parole intere: " + " ".join(kept[-5:]) if whole else
             f"attese «{' '.join(kept[-5:])}», sentite «{' '.join(w['w'] for w in heard if w['t0'] >= vd - 8)[-80:]}»")
        rep["heard"] = hw

    wps = len(kept) / max(vd, 0.1)
    line(True, "pace", f"{len(kept)} parole in {vd:.1f}s = {wps:.2f} parole/s")

    save_json(cd / "verify.json", rep)
    print(f"  report {cd / 'verify.json'}")
    if hard:
        sys.exit(f"✗ check falliti: {', '.join(hard)}")


if __name__ == "__main__":
    main()
