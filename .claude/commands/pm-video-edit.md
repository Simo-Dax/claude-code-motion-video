---
description: Montaggio video da girato o da video già generato → MP4 finito (tagli, silenzi, audio −14 LUFS, b-roll, screenshot, motion SA6B, caption, export, QA). Skill nativa 72_video_editing (SA6C).
argument-hint: [brand] [slug o cartella progetto] [formato 9:16/4:5/16:9]
---

# /pm-video-edit — Video Editing

Esegui la skill nativa **`directives/skills/72_video_editing/SKILL.md`** (SA6C — Video Editing).

Argomenti: $ARGUMENTS

## Cosa fare
1. Leggi la SKILL.md e i suoi `references/` (formats, edit_json, playbook, qa). Stile da `context/brand/video_style.md` (se manca → Step 0 dal template).
2. Cartella con `scripts/new_project.sh <brand> <slug>` se non esiste, poi `ingest.py`.
3. **🚦 GATE 1** formato + tagli + piano visivo + brief motion per SA6B → OK utente.
4. `cuts.json` → `plan.py` → rifinitura `edit.json` → `build.py --preview` → QA (`check_frames.py`, `verify_final.py`).
5. **🚦 GATE 2** preview + verdetto QA → finale → export. Output: `output/<brand>/25_Video_Edits/<slug>/_out/`.
6. Lingue in `note.md` → `/pm-localize`.
