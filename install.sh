#!/bin/bash
# Installa il pacchetto SA6B + SA6C nella root del repo performance-marketing-agent.
# Uso: ./install.sh /percorso/al/repo
set -euo pipefail
REPO="${1:?uso: ./install.sh /percorso/al/repo}"
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -f "$REPO/claude.md" ] && [ -d "$REPO/.claude/agents" ] || { echo "✗ $REPO non sembra il repo del team (manca claude.md o .claude/agents)"; exit 1; }

echo "→ copio agenti, command, skill native e template"
mkdir -p "$REPO/.claude/agents" "$REPO/.claude/commands" "$REPO/.claude/skills" "$REPO/directives/skills" "$REPO/context/brand"
cp "$HERE/.claude/agents/"*.md "$REPO/.claude/agents/"
cp "$HERE/.claude/commands/"*.md "$REPO/.claude/commands/"
for s in "$HERE/.claude/skills/"*; do
  n="$(basename "$s")"
  if [ -e "$REPO/.claude/skills/$n" ]; then echo "  = .claude/skills/$n esiste già, lo lascio"; else cp -R "$s" "$REPO/.claude/skills/"; echo "  + .claude/skills/$n"; fi
done
for s in "$HERE/directives/skills/"*; do cp -R "$s" "$REPO/directives/skills/"; echo "  + directives/skills/$(basename "$s")"; done
cp -n "$HERE/context/brand/video_style.template.md" "$REPO/context/brand/" || true
chmod +x "$REPO/directives/skills/72_video_editing/scripts/new_project.sh"

echo "→ controllo i tool locali"
for t in ffmpeg ffprobe whisper-cli node npx python3; do
  if command -v "$t" >/dev/null; then echo "  ✓ $t"; else echo "  ✗ $t mancante"; fi
done
python3 -c "import PIL" 2>/dev/null && echo "  ✓ Pillow" || echo "  ✗ Pillow mancante → pip3 install pillow"
M="${REEL_WHISPER_MODEL:-$HOME/.cache/whisper/ggml-large-v3-turbo-q5_0.bin}"
[ -f "$M" ] && echo "  ✓ modello whisper" || echo "  ✗ modello whisper mancante → scarica ggml-large-v3-turbo-q5_0.bin in ~/.cache/whisper/ (huggingface.co/ggerganov/whisper.cpp)"

cat <<MSG

Fatto. Passi manuali (vedi INTEGRAZIONE.md):
  1. brew install ffmpeg whisper-cpp   (se mancano)
  2. HeyGen: claude mcp add --transport http heygen https://mcp.heygen.com/mcp/v1/   (oppure il blocco in .mcp.json)
  3. Aggiorna claude.md, sa6_asset_production.md, 14_asset_production, COMMANDS.md come da INTEGRAZIONE.md
  4. Facoltativo: ./update_skills.sh per riprendere le ultime versioni delle skill esterne
MSG
