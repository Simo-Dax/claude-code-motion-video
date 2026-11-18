"""Shared helpers for the reel editor (skill 72_video_editing). Python 3.9, stdlib + Pillow."""
import json
import os
import subprocess
import sys
from pathlib import Path

VIDEO_EXT = {".mov", ".mp4", ".m4v", ".hevc"}
AUDIO_EXT = {".m4a", ".wav", ".mp3", ".aac", ".caf", ".aif", ".aiff"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".heic"}

W, H, FPS = 1080, 1920, 30
WHISPER_MODEL = os.environ.get(
    "REEL_WHISPER_MODEL",
    str(Path.home() / ".cache/whisper/ggml-large-v3-turbo-q5_0.bin"),
)


def run(cmd, quiet=True):
    """Run a command, raise with stderr tail on failure."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        tail = "\n".join(r.stderr.strip().splitlines()[-15:])
        sys.exit(f"✗ command failed: {' '.join(map(str, cmd[:6]))} …\n{tail}")
    if not quiet:
        print(r.stdout)
    return r.stdout


def ffprobe(path):
    out = run(["ffprobe", "-v", "error", "-print_format", "json",
               "-show_format", "-show_streams", str(path)])
    return json.loads(out)


def work(reel):
    d = Path(reel) / "_work"
    d.mkdir(exist_ok=True)
    return d


def load_json(p):
    with open(p) as f:
        return json.load(f)


def save_json(p, data):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def key(src):
    """clips/IMG_0012.MOV -> clips__IMG_0012 (stable file key for _work artefacts)."""
    return src.replace("/", "__").rsplit(".", 1)[0]
