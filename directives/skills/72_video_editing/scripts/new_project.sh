#!/bin/bash
# Crea una cartella progetto video dal template: output/<brand>/25_Video_Edits/<YYYY-MM-DD>-<slug>/
set -euo pipefail
brand="${1:?uso: new_project.sh <brand> <slug>}"
slug="${2:?uso: new_project.sh <brand> <slug>}"
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../../../.." && pwd)"
dest="$root/output/$brand/25_Video_Edits/$(date +%Y-%m-%d)-$slug"
[ -e "$dest" ] && { echo "✗ esiste già: $dest"; exit 1; }
mkdir -p "$(dirname "$dest")"
cp -R "$here/../templates/video_project" "$dest"
find "$dest" -name .keep -delete
echo "✓ $dest"
echo "  clip in clips/, voce in voiceover/, screenshot in overlays/, compila note.md"
