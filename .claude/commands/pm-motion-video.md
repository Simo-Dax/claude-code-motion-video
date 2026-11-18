---
description: Grafiche animate dentro un video parlato (hook, cutaway sulle parole, lista con spunte, split screen 1080x960, CTA, b-roll animato, soggetto scontornato) con template keynote, motion-graphics, motion-broll, object-separation. Skill nativa 74_motion_in_video (SA6B).
argument-hint: [cartella progetto 25_Video_Edits] [scene dal brief motion di SA6C]
---

# /pm-motion-video — Motion in Video

Esegui la skill nativa **`directives/skills/74_motion_in_video/SKILL.md`** (SA6B — Motion Graphics).

Argomenti: $ARGUMENTS

## Cosa fare
1. Leggi la SKILL.md, `context/brand/motion.md`, `/hyperframes` + `/hyperframes-core`.
2. Brief motion (una riga per scena: tempo, parola d'aggancio, layout, motore, testo esatto) dentro il **🚦 GATE 1** di `72`.
3. Tempi parola sul timeline finale (whisper sulla preview di `72`).
4. Build per scena in `<project>/motion/<scena>/`, `npx hyperframes check`, 2 frame per scena → **🚦 GATE 2**.
5. Render (fuori dal sandbox se serve) → path e durate a SA6C per `edit.json`.
