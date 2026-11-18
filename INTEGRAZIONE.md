# Integrazione nel repo del team

`install.sh` copia i file. Queste sono le modifiche a mano ai file che esistono già, così l'orchestrator sa che SA6B e SA6C ci sono e quando chiamarli. Sono 5 file, in quest'ordine.

## 1. `claude.md`

**Architettura**: sotto la riga di `sa6_asset_production` aggiungi:

```
├── sa6b_motion_graphics      ← motion in codice: ad motion (67) + motion dentro i video (74) (da SA5+SA7 o brief SA6C)
├── sa6c_video_editing        ← montaggio (72), caption, export, localizzazione HeyGen (73) (da girato o video SA6/SA6B)
```

**Flusso pipeline creativa**: sostituisci `→ SA7 → SA6 → consolidation` con:

```
→ SA7 → SA6 (statiche, UGC, formati AI) ∥ SA6B (motion) → SA6C (montaggio, caption, lingue) → consolidation
```

**Come si invocano gli agenti**: "I 9 sub-agent" → "Gli 11 sub-agent". Esempio di `subagent_type`: aggiungi `sa6b-motion-graphics`, `sa6c-video-editing`.

**Tabella agente → skill**: la riga SA6 perde `67 motion_design` e `63 auto_captions`, e si aggiungono:

```
| **SA6B** Motion Graphics | 67 motion_design (ad motion autonome) · 74 motion_in_video (motion dentro un video) · skill HyperFrames · motion-broll · object-separation · gsap-* · animate/review-animations |
| **SA6C** Video Editing | 72 video_editing · 63 auto_captions · 73 video_localization (HeyGen) · talking-head-recut · embedded-captions |
```

**Gate**: aggiungi alla lista dei gate umani sull'orchestrator: 🚦GATE 1 e 🚦GATE 2 di SA6B (brief, preview), 🚦GATE 1 e 🚦GATE 2 di SA6C (tagli e piano, preview), 🚦GATE LINGUE di SA6C (lingue, consenso voce, crediti HeyGen). I subagent ritornano la proposta e si fermano.

**Cartelle output**: dopo `24_Format_Changes/ ← 71` aggiungi `· 25_Video_Edits/ ← 72 (motion/ ← 74, _out/loc/<lingua>/ ← 73)`.

**Note di sistema**: la riga "Motion design (`67`): lane SA6…" diventa "lane **SA6B**". Aggiungi:

```
- **Video editing (`72`) e localizzazione (`73`):** lane SA6C. Montaggio locale (ffmpeg + whisper.cpp + script Python), caption Pillow, QA misurato. HeyGen via MCP ufficiale (OAuth, crediti del piano) o CLI con API key: dubbing con lip-sync, con o senza sottotitoli. Stile in `context/brand/video_style.md`.
```

## 2. `.claude/agents/sa6_asset_production.md`

Nel **Skill router**:
- "Serve una **motion graphic** … → `67_motion_design`" → "… → **SA6B** (`sa6b-motion-graphics`)".
- "**Video finito che vuole le caption** → `63_auto_captions`" → "→ **SA6C** (`63_auto_captions`, o `72_video_editing` se servono anche tagli o grafiche)".
- Aggiungi: "Serve **montare girato** (clip del cliente, founder, testimonial veri) o **localizzare** un video in altre lingue → **SA6C** (`sa6c-video-editing`)".

Nel **Handoff** aggiungi: "Video UGC/podcast/Pixar finiti che devono essere tagliati, vestiti con caption e grafiche o tradotti → SA6C".

## 3. `directives/skills/14_asset_production.md`

Nella logica di routing (riga "0. Il concept ha Formato primario = motion graphics…") lascia `67_motion_design` ma indica l'agente: "→ SÌ → **SA6B** → `67_motion_design`". Aggiungi un passo:

```
0b. Il concept parte da girato reale (founder, cliente, testimonial, demo registrata) o un video finito va montato, sottotitolato o tradotto?
   → SÌ → SA6C → 72_video_editing (+ 73_video_localization se ci sono lingue)
```

E nella lane ANIMAZIONE del gate formato: `67` motion graphics → "SA6B: `67` motion graphics, `74` motion dentro un video".

## 4. `.claude/agents/sa5_creative_concepts.md`

In "Esecuzione raccomandata" aggiungi le lane `74` (motion dentro un video) e `72` (girato da montare): `[STATICA / ANIMAZIONE + lane 67/74/56/62/58-61/64 / GIRATO + 72]`.

## 5. `COMMANDS.md`

Nuova sezione dopo "Produzione (SA6)":

```
## Motion e video (SA6B, SA6C)
| Comando | Cosa fa | Skill / Agente |
|---------|---------|----------------|
| `/pm-motion` | Ad motion in codice → MP4 (spostato da SA6) | 67 / SA6B |
| `/pm-motion-video` | Grafiche animate dentro un video parlato: hook, cutaway sulle parole, lista, split screen, CTA | 74 / SA6B |
| `/pm-video-edit` | Montaggio da girato: tagli, silenzi, audio −14 LUFS, b-roll, motion, caption, export, QA | 72 / SA6C |
| `/pm-captions` | Caption stile locked su un video finito (spostato da SA6) | 63 / SA6C |
| `/pm-localize` | Dubbing HeyGen con lip-sync, con o senza sottotitoli, o solo sottotitoli tradotti | 73 / SA6C |
```

E togli `/pm-motion` e `/pm-captions` dalla tabella SA6. Aggiorna `.claude/commands/pm-motion.md` e `pm-captions.md`: "(SA6)" → "(SA6B)" e "(SA6C)".

## Setup macchina (una volta)

```bash
brew install ffmpeg whisper-cpp
pip3 install pillow
mkdir -p ~/.cache/whisper && curl -L -o ~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
npx hyperframes telemetry disable
claude mcp add --transport http heygen https://mcp.heygen.com/mcp/v1/    # login OAuth al primo uso
```

Per HeyGen via API (proofread dei sottotitoli, batch multi-lingua): CLI `heygen` e `heygen auth login` con la API key presa da app.heygen.com → Settings → API. La chiave non va nel repo.

Nel `.mcp.json` del repo, in alternativa al comando:

```json
"heygen": {"type": "http", "url": "https://mcp.heygen.com/mcp/v1/"}
```

## Verifica dopo l'installazione

1. Apri Claude Code nel repo e chiedi: "quali subagent hai?" → devono comparire `sa6b-motion-graphics` e `sa6c-video-editing`.
2. Test motion: `/pm-motion-video` su un progetto di prova, una scena `scene-titolo` → render in ~15 s.
3. Test montaggio: `/pm-video-edit` con una clip da 20-30 s → preview + verdetto QA.
4. Test lingue: `/pm-localize` su quel video, una lingua, `mode: speed` (costa meno) → video doppiato.
