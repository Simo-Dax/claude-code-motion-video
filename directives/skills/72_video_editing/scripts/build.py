"""Step 3 — render the reel from edit.json (audio clean-up, cuts, b-roll, overlays, captions, export).

Usage:  python3 directives/skills/72_video_editing/scripts/build.py <reel_dir> [--preview]

--preview  → _out/preview.mp4 (540x960, fast) for GATE 2
default    → _out/<reel_name>.mp4 (1080x1920, H.264 High, yuv420p bt709, AAC 48k, -14 LUFS) + captions.srt
"""
import argparse
import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import FPS, H, IMAGE_EXT, W, ffprobe, load_json, run

FONT = os.environ.get("VIDEO_FONT", "/System/Library/Fonts/HelveticaNeue.ttc")  # brand font: set VIDEO_FONT (+ VIDEO_FONT_INDEX)
BOLD_DEFAULT = int(os.environ.get("VIDEO_FONT_INDEX", "1"))
BOLD = BOLD_DEFAULT
VOICE_CHAIN = ("highpass=f=80,afftdn=nr=12:nf=-40:tn=1,deesser=i=0.4,"
               "acompressor=threshold=0.125:ratio=3:attack=5:release=100:makeup=2,"
               "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000")
# "audio_chain": "open" — lighter denoise + EQ (less boxy 330Hz, presence 3.2k, air 8k): iPhone at arm's length
# sounds muffled with VOICE_CHAIN (16/10/2026, reel Black Friday)
VOICE_CHAIN_OPEN = ("highpass=f=75,afftdn=nr=6:nf=-48:tn=1,equalizer=f=140:t=q:w=0.9:g=2,"
                    "equalizer=f=330:t=q:w=1.1:g=-4.5,equalizer=f=800:t=q:w=1.5:g=-1,"
                    "equalizer=f=3200:t=q:w=1.0:g=5,highshelf=f=8000:g=4.5,deesser=i=0.35:m=0.5:f=0.5,"
                    "acompressor=threshold=0.1:ratio=2.5:attack=12:release=160:makeup=1.5,"
                    "loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000")


# ---------- audio ----------

def build_audio(reel, edit, bd):
    segs = []
    for i, s in enumerate(edit["spine"]):
        f = bd / f"seg_{i:03d}.wav"
        d = s["out"] - s["in"]
        run(["ffmpeg", "-v", "error", "-ss", str(s["in"]), "-t", f"{d:.3f}", "-i", str(reel / s["src"]),
             "-vn", "-ac", "1", "-ar", "48000", "-af",
             f"afade=t=in:d=0.008,afade=t=out:st={max(d - 0.012, 0):.3f}:d=0.012",
             "-c:a", "pcm_s16le", "-y", str(f)])
        segs.append(f)
    lst = bd / "segs.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in segs))
    joined = bd / "joined.wav"
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-y", str(joined)])
    voice = bd / "voice.wav"
    chain = VOICE_CHAIN if edit.get("audio_cleanup", True) else "loudnorm=I=-14:TP=-1.5,aresample=48000"
    if edit.get("audio_chain"):  # per-reel override, e.g. VOICE_CHAIN_OPEN for muffled recordings
        chain = VOICE_CHAIN_OPEN if edit["audio_chain"] == "open" else edit["audio_chain"]
    run(["ffmpeg", "-v", "error", "-i", str(joined), "-af", chain, "-ac", "2", "-y", str(voice)])
    m = edit.get("music")
    if not m:
        return voice
    dur = edit["duration"]
    mixed = bd / "mix.wav"
    run(["ffmpeg", "-v", "error", "-i", str(voice), "-stream_loop", "-1", "-i", str(reel / m["file"]),
         "-filter_complex",
         f"[1:a]atrim=0:{dur},volume={m.get('db', -22)}dB,afade=t=out:st={max(dur - 1.5, 0)}:d=1.5[m];"
         "[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89",
         "-ar", "48000", "-y", str(mixed)])
    return mixed


# ---------- video ----------

def sdr_source(reel, src, info, bd):
    """iPhone HDR (HLG/Dolby Vision) → SDR bt709 via VideoToolbox, cached. Without it colours look washed out."""
    out = bd / "sdr" / (Path(src).stem + ".mp4")
    if out.exists():
        return out
    out.parent.mkdir(exist_ok=True)
    rot = info.get("rotation", 0) % 360
    fix = {90: ",transpose=2", 180: ",hflip,vflip", 270: ",transpose=1"}.get(rot, "")
    run(["ffmpeg", "-v", "error", "-hwaccel", "videotoolbox", "-hwaccel_output_format", "videotoolbox_vld",
         "-noautorotate", "-i", str(reel / src),
         "-vf", "scale_vt=color_matrix=bt709:color_primaries=bt709:color_transfer=bt709,"
                f"hwdownload,format=p010le,format=yuv420p{fix}",  # iPhone HLG is 10-bit: nv12 download fails
         "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-c:a", "copy", "-y", str(out)])
    return out


# every shot gets identical colour tags: a mid-stream change makes ffmpeg re-init the
# final filtergraph and silently drop the caption layer from that point on
TAIL = (f"scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,"
        f"setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709,setsar=1,fps={FPS}")


def fit(s, dur, ch=H):
    """Zoom + crop of a camera/b-roll shot. ch < H crops a band of that height (split layout face)."""
    z = s.get("zoom", 1.0)
    # "fy": vertical zoom anchor (0 = top, 0.5 = centre; ~0.3 keeps the face in frame on punch-ins)
    # "push": extra zoom gained across the shot (slow dolly-in, e.g. 0.025)
    fy, push = s.get("fy", 0.5), s.get("push", 0)
    if push:
        zt = f"({z}+{push}*t/{dur:.3f})"
        scale = (f"scale=w='trunc({W}*{zt}/2)*2':h='trunc({H}*{zt}/2)*2':eval=frame,")
    else:
        scale = f"scale=w={round(W * z)}:h={round(H * z)}:force_original_aspect_ratio=increase,"
    return f"{scale}crop={W}:{ch}:(iw-{W})/2:(ih-{ch})*{fy}"


def shot_input(reel, src_rel, t_in, info, bd):
    src = reel / src_rel
    if src.suffix.lower() in IMAGE_EXT:
        return ["-loop", "1", "-i", str(src)]
    e = info.get(src_rel, {})
    if e.get("hdr"):
        src = sdr_source(reel, src_rel, e, bd)
    return ["-ss", str(t_in), "-i", str(src)]


def build_video(reel, edit, probe, bd):
    shots = edit["shots"]
    if not shots:
        raise SystemExit("✗ edit.json: 'shots' vuoto — assegna le b-roll prima del build")
    total = sum(s["dur"] for s in shots)
    if total < edit["duration"] - 0.05:
        raise SystemExit(f"✗ shots coprono {total:.2f}s ma l'audio dura {edit['duration']:.2f}s")
    info = {e["src"]: e for e in probe["sources"]}
    sd = bd / "shots"
    shutil.rmtree(sd, ignore_errors=True)
    sd.mkdir()
    files, t = [], 0.0
    for i, s in enumerate(shots):
        if t >= edit["duration"] - 1e-3:
            break
        dur = min(s["dur"], edit["duration"] - t)
        frames = round((t + dur) * FPS) - round(t * FPS)      # frame-exact, no drift vs audio
        t += dur
        grade = edit["grade"] + "," if edit.get("grade") and not s["src"].startswith("motion/") else ""
        inp = shot_input(reel, s["src"], s.get("in", 0), info, bd)   # light colour correction: camera only
        sp = s.get("split")
        if sp:
            # split layout (references/formats.md, split screen): graphic on top, face below, face keeps running
            th = round(H * sp.get("ratio", 0.5) / 2) * 2
            inp += shot_input(reel, sp["top"], sp.get("in", 0), info, bd)
            vmap = ["-filter_complex",
                    f"[0:v]{grade}{fit(s, dur, H - th)}[f];"
                    f"[1:v]scale={W}:{th}:force_original_aspect_ratio=increase,crop={W}:{th}[g];"
                    f"[g][f]vstack=inputs=2,{TAIL}[v]", "-map", "[v]"]
        else:
            vmap = ["-vf", f"{grade}{fit(s, dur)},{TAIL}"]
        f = sd / f"{i:03d}.mp4"
        run(["ffmpeg", "-v", "error", *inp, "-frames:v", str(frames), *vmap, "-an",
             "-c:v", "libx264", "-crf", "14", "-preset", "veryfast", "-r", str(FPS), "-y", str(f)])
        files.append(f)
    lst = sd / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in files))
    video = bd / "video.mp4"
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-y", str(video)])
    return video


# ---------- graphics ----------

def caption_png(text, out, size=62, deep=False):
    """Reference style: white Helvetica Neue Bold, one line, soft shadow, no box.
    deep=True ("caption_shadow": "deep"): tight contact shadow + wide soft halo, text lifts off the video."""
    font = ImageFont.truetype(FONT, size, index=BOLD)
    lines = [text]
    max_w = W - 260   # centred, right edge ≤ 950: IG button column covers the right 130px (QA 28/10/2026)
    while font.getlength(text) > max_w and size > 50:
        size -= 2
        font = ImageFont.truetype(FONT, size, index=BOLD)
    if font.getlength(text) > max_w:                       # still too long → two balanced lines
        words = text.split()
        best = min(range(1, len(words)), key=lambda k: abs(
            font.getlength(" ".join(words[:k])) - font.getlength(" ".join(words[k:]))))
        lines = [" ".join(words[:best]), " ".join(words[best:])]
    lh = int(size * 1.18)
    ch = 60 + lh * len(lines)
    canvas = Image.new("RGBA", (W, ch), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, ch), (0, 0, 0, 0))
    ds, dt = ImageDraw.Draw(shadow), ImageDraw.Draw(canvas)
    for n, line in enumerate(lines):
        x = (W - font.getlength(line)) / 2
        y = 30 + n * lh
        ds.text((x, y + 3), line, font=font, fill=(0, 0, 0, 150))
        dt.text((x, y), line, font=font, fill=(255, 255, 255, 255))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    if deep:
        halo = Image.new("RGBA", (W, ch), (0, 0, 0, 0))
        contact = Image.new("RGBA", (W, ch), (0, 0, 0, 0))
        dh, dc = ImageDraw.Draw(halo), ImageDraw.Draw(contact)
        for n, line in enumerate(lines):
            x, y = (W - font.getlength(line)) / 2, 30 + n * lh
            dh.text((x, y + 8), line, font=font, fill=(0, 0, 0, 200), stroke_width=6, stroke_fill=(0, 0, 0, 200))
            dc.text((x, y + 4), line, font=font, fill=(0, 0, 0, 170))
        shadow = Image.alpha_composite(halo.filter(ImageFilter.GaussianBlur(16)),
                                       Image.alpha_composite(shadow, contact.filter(ImageFilter.GaussianBlur(2))))
    Image.alpha_composite(shadow, canvas).save(out)
    return ch


def overlay_png(src, out, width, radius=28):
    """Screenshot/picture card: rounded corners + soft drop shadow."""
    im = Image.open(src).convert("RGBA")
    w = int(W * width)
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, *im.size], radius=radius, fill=255)
    im.putalpha(mask)
    pad = 40
    card = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 10, pad + im.width, pad + im.height + 10],
                                         radius=radius, fill=(0, 0, 0, 110))
    card = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), card)
    card.alpha_composite(im, (pad, pad))
    card.save(out)
    return card.size


def srt(caps, out):
    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    out.write_text("".join(f"{i + 1}\n{ts(c['t0'])} --> {ts(c['t1'])}\n{c['text']}\n\n"
                           for i, c in enumerate(caps)))


# ---------- final ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reel")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    reel = Path(a.reel).resolve()
    edit = load_json(reel / "edit.json")
    probe = load_json(reel / "_work" / "probe.json")
    bd = reel / "_work" / "build"
    bd.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(reel).free / 1e9
    if free < 2:
        raise SystemExit(f"✗ solo {free:.1f} GB liberi: libera spazio prima del build (HyperFrames muore sotto ~0.5)")
    if free < 5:
        print(f"⚠️ {free:.1f} GB liberi: render in sequenza, cancella _work/build/shots dopo il finale")
    od = reel / "_out"
    od.mkdir(exist_ok=True)

    audio = build_audio(reel, edit, bd)
    video = build_video(reel, edit, probe, bd)
    print("✓ audio + tagli")

    gd = bd / "gfx"
    shutil.rmtree(gd, ignore_errors=True)
    gd.mkdir()
    inputs = ["-reinit_filter", "0", "-i", str(video), "-i", str(audio)]
    graph, last, n = [], "0:v", 2

    for i, o in enumerate(edit.get("overlays", [])):
        src = reel / o["file"]
        if src.suffix.lower() in {".mov", ".webm"}:
            # full-frame alpha video (HyperFrames --format mov = ProRes 4444), e.g. hook title over the face
            inputs += ["-i", str(src)]
            graph.append(f"[{n}:v]fps={FPS},format=yuva420p,setpts=PTS+{o['t0']}/TB[o{i}]")
            graph.append(f"[{last}][o{i}]overlay=0:0:eof_action=pass[vo{i}]")
            last, n = f"vo{i}", n + 1
            continue
        png = gd / f"ov_{i}.png"
        if src.suffix.lower() == ".heic":
            conv = gd / f"ov_{i}_src.png"
            run(["sips", "-s", "format", "png", str(src), "--out", str(conv)])
            src = conv
        cw, chh = overlay_png(src, png, o.get("width", 0.82))
        d = o["t1"] - o["t0"]
        x, y = (W - cw) // 2, int(o.get("y", 760) - chh / 2)
        inputs += ["-loop", "1", "-framerate", str(FPS), "-t", f"{d:.3f}", "-i", str(png)]
        graph.append(f"[{n}:v]format=rgba,fade=t=in:st=0:d=0.18:alpha=1,"
                     f"fade=t=out:st={max(d - 0.18, 0):.3f}:d=0.18:alpha=1,"
                     f"setpts=PTS+{o['t0']}/TB[o{i}]")
        graph.append(f"[{last}][o{i}]overlay={x}:{y}:eof_action=pass[vo{i}]")
        last, n = f"vo{i}", n + 1

    # All captions = ONE input: concat demuxer of full-frame PNGs with durations (blank in gaps).
    # (One input per caption either drops captions after ~8s or deadlocks ffmpeg 8.)
    cy = edit.get("caption_y", 1420)
    blank = gd / "blank.png"
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
    lines, t = [], 0.0
    for i, c in enumerate(edit["captions"]):
        if c["t0"] > t + 1e-3:
            lines += [f"file '{blank.name}'", f"duration {c['t0'] - t:.3f}"]
        strip = gd / f"cap_{i:03d}_strip.png"
        ch = caption_png(c["text"], strip, size=c.get("size", 62),   # per-caption override
                         deep=edit.get("caption_shadow") == "deep")
        frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        # per-caption "y": split sections put captions on the seam (~960), full-frame ones stay at caption_y
        frame.alpha_composite(Image.open(strip), (0, int(c.get("y", cy) - ch / 2)))
        frame.save(gd / f"cap_{i:03d}.png")
        lines += [f"file 'cap_{i:03d}.png'", f"duration {c['t1'] - max(c['t0'], t):.3f}"]
        t = c["t1"]
    lines += [f"file '{blank.name}'", f"duration {max(edit['duration'] - t, 0.1):.3f}", f"file '{blank.name}'"]
    (gd / "captions.txt").write_text("\n".join(lines) + "\n")
    inputs += ["-f", "concat", "-safe", "0", "-i", str(gd / "captions.txt")]
    graph.append(f"[{n}:v]fps={FPS},format=rgba[caps]")
    graph.append(f"[{last}][caps]overlay=0:0:eof_action=pass[vcap]")
    last, n = "vcap", n + 1

    tail = "scale=540:960," if a.preview else ""
    graph.append(f"[{last}]{tail}format=yuv420p,setsar=1[vout]")
    name = "preview.mp4" if a.preview else f"{reel.name}.mp4"
    out = od / name
    # preview: un fotogramma chiave al secondo (-g 30), così nel player della Studio il salto avanti/indietro è immediato
    enc = (["-c:v", "libx264", "-preset", "ultrafast", "-crf", "30", "-g", "30"] if a.preview else
           ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high"])
    script = bd / "graph.txt"
    script.write_text(";\n".join(graph))
    run(["ffmpeg", "-v", "error", *inputs, "-filter_complex_script", str(script),
         "-map", "[vout]", "-map", "1:a", *enc, "-r", str(FPS),
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
         "-t", f"{edit['duration']:.3f}", "-y", str(out)])
    srt(edit["captions"], od / "captions.srt")

    info = ffprobe(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = next(s for s in info["streams"] if s["codec_type"] == "audio")
    dur = float(info["format"]["duration"])
    print(f"✓ {out}\n  {v['width']}x{v['height']} {v['codec_name']} {v['pix_fmt']} {v.get('color_space', '?')}"
          f" · {au['codec_name']} {au['sample_rate']}Hz · {dur:.2f}s (atteso {edit['duration']:.2f}s)"
          f" · {len(edit['captions'])} caption · {len(edit.get('overlays', []))} overlay")
    if abs(dur - edit["duration"]) > 0.1:
        raise SystemExit("✗ durata output diversa da edit.json")


if __name__ == "__main__":
    main()
