"""Step 2 — from the approved cut list to a draft edit (spine audio + captions + shots).

Usage:  python3 directives/skills/72_video_editing/scripts/plan.py <reel_dir>

Reads  <reel_dir>/_work/cuts.json  (written by Claude after GATE 1):
{
  "takes": [                                   # in reel order
    {"src": "voiceover/vo.m4a", "from": 0, "to": 212, "drop": [3, 4, "40-47"]}
  ],
  "max_pause": 0.35                            # longer silences are cut
}
Writes <reel_dir>/edit.json:
  spine     audio segments kept, in order (src, in, out — seconds on the source)
  captions  2-4 word chunks on the OUTPUT timeline, text = whisper words (fix typos, never reword)
  shots     video track. Talking-head takes are pre-filled in sync (zoom alternates on jump cuts);
            voiceover-only takes leave it empty → Claude fills it with b-roll
  overlays  [] → Claude adds screenshots {file, t0, t1, width, y}
"""
import sys
from pathlib import Path

from common import key, load_json, save_json

HEAD_PAD, TAIL_PAD = 0.06, 0.12
MAX_WORDS, MAX_CHARS = 4, 24


def expand(drop):
    ids = set()
    for d in drop:
        if isinstance(d, str) and "-" in d:
            a, b = d.split("-")
            ids.update(range(int(a), int(b) + 1))
        else:
            ids.add(int(d))
    return ids


def segments(words, take, max_pause):
    """Group kept words into continuous source segments."""
    drop = expand(take.get("drop", []))
    lo, hi = take.get("from", 0), take.get("to", len(words) - 1)
    segs, cur = [], []
    for w in words[lo:hi + 1]:
        if w["id"] in drop:
            if cur:
                segs.append(cur)
            cur = []
            continue
        if cur and (w["id"] != cur[-1]["id"] + 1 or w["t0"] - cur[-1]["t1"] > max_pause):
            segs.append(cur)
            cur = []
        cur.append(w)
    if cur:
        segs.append(cur)
    out = []
    for s in segs:
        first, last = s[0], s[-1]
        prev = words[first["id"] - 1]["t1"] if first["id"] > 0 else 0.0
        nxt = words[last["id"] + 1]["t0"] if last["id"] + 1 < len(words) else last["t1"] + TAIL_PAD
        out.append({
            "in": round(max(first["t0"] - HEAD_PAD, prev, 0.0), 3),
            "out": round(min(last["t1"] + TAIL_PAD, max(nxt, last["t1"])), 3),
            "words": s,
        })
    return out


def clean(text):
    return " ".join(w.rstrip(".,;:…") for w in text.split()).strip()


WEAK = {"il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "e", "o", "ma", "di", "a", "da", "in",
        "con", "su", "per", "tra", "fra", "al", "allo", "alla", "ai", "agli", "alle", "del", "dello",
        "della", "dei", "degli", "delle", "nel", "nella", "sul", "sulla", "che", "non", "mi", "ti",
        "ci", "vi", "si", "come", "se", "è", "the", "a", "an", "of", "to", "and"}


def split_phrase(ph):
    """One spoken phrase → balanced chunks of ≤4 words / ≤24 chars, never ending on a weak word."""
    n = len(ph)
    chars = len(" ".join(w[0] for w in ph))
    k = max(-(-n // MAX_WORDS), -(-chars // MAX_CHARS), 1)
    k = min(k, n)
    size = n / k
    fixed = []
    for j in range(1, k):
        ideal, lo = round(size * j), (fixed[-1] if fixed else 0)

        def cost(c):   # distance from balance + weak ending + one-word orphans + overlong chunks
            left, rest = c - lo, n - c
            return (abs(c - ideal) + 5 * (ph[c - 1][0].lower().strip(",.") in WEAK)
                    + 3 * (left == 1) + 3 * (rest == 1) + 10 * (left > MAX_WORDS))
        fixed.append(min(range(lo + 1, n), key=cost))
    bounds = [0] + fixed + [n]
    return [ph[a:b] for a, b in zip(bounds, bounds[1:]) if b > a]


def captions(timed):
    """timed = [(word, t0_out, t1_out)] → phrases (punctuation / pause > 0.4s) → 2-4 word chunks."""
    phrases, cur = [], []
    for i, (w, t0, t1) in enumerate(timed):
        cur.append((w, t0, t1))
        nxt = timed[i + 1] if i + 1 < len(timed) else None
        if nxt is None or w[-1] in ".,?!;:" or nxt[1] - t1 > 0.4:
            phrases.append(cur)
            cur = []
    chunks = []
    for ph in phrases:
        if chunks and len(ph) == 1 and len(chunks[-1]) < MAX_WORDS:
            chunks[-1] = chunks[-1] + ph           # no one-word orphans
        else:
            chunks.extend(split_phrase(ph))
    caps = []
    for i, c in enumerate(chunks):
        start, end = c[0][1], c[-1][2]
        if i + 1 < len(chunks) and chunks[i + 1][0][1] - end < 0.5:
            end = chunks[i + 1][0][1]          # no flicker between consecutive chunks
        else:
            end += 0.2
        caps.append({"t0": round(start, 3), "t1": round(end, 3),
                     "text": clean(" ".join(x[0] for x in c))})
    return caps


def main():
    reel = Path(sys.argv[1])
    wd = reel / "_work"
    cuts = load_json(wd / "cuts.json")
    max_pause = cuts.get("max_pause", 0.35)

    spine, shots, timed, t = [], [], [], 0.0
    for take in cuts["takes"]:
        words = load_json(wd / "words" / f"{key(take['src'])}.json")
        is_video = take["src"].startswith("clips/")
        for n, seg in enumerate(segments(words, take, max_pause)):
            dur = seg["out"] - seg["in"]
            spine.append({"src": take["src"], "in": seg["in"], "out": seg["out"]})
            if is_video:
                shots.append({"src": take["src"], "in": seg["in"], "dur": round(dur, 3),
                              "zoom": 1.0 if n % 2 == 0 else 1.08})
            for w in seg["words"]:
                timed.append((w["w"], t + w["t0"] - seg["in"], t + w["t1"] - seg["in"]))
            t += dur

    edit = {
        "duration": round(t, 3),
        "spine": spine,
        "captions": captions(timed),
        "shots": shots,
        "overlays": [],
        "music": None,
        "caption_style": "clean",
    }
    save_json(reel / "edit.json", edit)
    kept = sum(1 for _ in timed)
    print(f"✓ edit.json  durata {t:.1f}s · {len(spine)} segmenti · {kept} parole · "
          f"{len(edit['captions'])} caption · {len(shots)} shot")
    if not shots:
        print("  ⚠️ solo voiceover: riempi 'shots' con b-roll (somma dur = durata)")


if __name__ == "__main__":
    main()
