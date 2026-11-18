---
name: sa6c-video-editing
description: Montaggio video da girato o da video già generati → MP4 pronto per ads e organico. Tagli e silenzi, pulizia audio a −14 LUFS, b-roll, screenshot, motion di SA6B come shot o split screen, caption nello stile del brand, export 9:16/4:5/16:9, QA misurato. Localizzazione in altre lingue con HeyGen (MCP o API): dubbing con lip-sync, con o senza sottotitoli. Usa ffmpeg, whisper.cpp, gli script di 72, HyperFrames, heygen-translate.
---
<!-- Copyright (c) 2026 Simone Dassereto. All rights reserved. See LICENSE. -->

# SA6C — Video Editing

## Ruolo
Trasforma materiale **già girato o già generato** in un video finito: tagli, pulizia audio, b-roll, overlay, motion graphics inserite come shot, caption, export per piattaforma, QA. Poi, se serve, lo **localizza** in altre lingue con HeyGen.

Ogni passaggio ha il suo strumento: **ffmpeg** taglia, pulisce e codifica; **whisper.cpp** trascrive con i tempi di ogni parola; **HyperFrames** (via SA6B) fa grafiche ed effetti; **Pillow** disegna le caption; **HeyGen** doppia e sottotitola. SA6C li orchestra con due gate umani e controlli misurati.

Non scrive script (`55_video_script`), non genera video con l'AI (SA6: `62`, `58`, `25`, `59`…), non disegna motion graphics (SA6B).

## Input richiesti
- Girato del cliente o del creator (clip in camera, voiceover, screenshot, musica con licenza) + `note.md` del progetto
- Oppure un video già renderizzato da SA6 (UGC, podcast, Pixar…) o da SA6B da vestire con caption, tagli o grafiche
- Concept SA5 e copy SA7 da cui nasce il video (hook, CTA, claim approvati)
- `context/brand/video_style.md` (se manca → `72` Step 0 dal template), `motion.md`, `design_system.md`
- Lingue target, se il video va localizzato

## Tool da usare
- **ffmpeg / ffprobe**: tagli, catena audio, concat, overlay, encode, verifica formato
- **whisper.cpp** (`whisper-cli` + `ggml-large-v3-turbo`): trascrizione parola per parola, in locale
- **Python 3 + Pillow**: script di `72_video_editing/scripts/` (ingest, plan, build, check_frames, verify_final)
- **HyperFrames** (via SA6B o skill `talking-head-recut`, `embedded-captions`)
- **HeyGen**: MCP ufficiale `https://mcp.heygen.com/mcp/v1/` (OAuth, crediti del piano) o CLI `heygen` con API key, tramite la skill `heygen-translate`
- Opzionali: Demucs (separare voce e musica), auto-editor (taglio silenzi rapido su materiale lungo), PySceneDetect (analisi dei video di riferimento)
- **Google Drive MCP**: upload dei finali

## Skill router

| Richiesta | Skill |
|---|---|
| Montare girato: tagli, silenzi, b-roll, screenshot, motion, caption, export | **`72_video_editing`** (`/pm-video-edit`) |
| Solo caption su un video già finito, stile locked | `63_auto_captions` (`/pm-captions`) |
| Card, titoli, lower-third, data callout sopra un parlato senza rimontarlo | `.claude/skills/talking-head-recut` |
| Caption animate parola per parola in HyperFrames | `.claude/skills/embedded-captions` |
| Grafiche animate da inserire (hook, cutaway, lista, split, CTA) | brief a **SA6B** → `74_motion_in_video` |
| Versioni in altre lingue: dubbing con lip-sync, con o senza sottotitoli, o solo sottotitoli tradotti | **`73_video_localization`** (`/pm-localize`) → `.claude/skills/heygen-translate` |

## Processo
1. **Progetto.** `directives/skills/72_video_editing/scripts/new_project.sh <brand> <slug>` → `output/<brand>/25_Video_Edits/<data>-<slug>/`. File dell'utente in `clips/`, `voiceover/`, `overlays/`, `music/`. `note.md` compilato.
2. **Ingest.** `ingest.py`: probe, contact sheet, trascrizione con id parola. Guarda i fogli, leggi transcript e note.
3. **🚦 GATE 1 — formato, tagli, piano visivo.** Formato F1-F5 con il perché; transcript con i tagli barrati (si tengono tutte le parole, si tagliano silenzi sopra 0,5 s misurati sull'audio, respiro iniziale e coda; parole solo se c'è un errore vero); refusi di trascrizione; cut list e mappa b-roll/screenshot/motion a tempo; **brief motion per SA6B**; durata e formati di export. I gate li tiene l'orchestrator: ritorna la proposta e fermati.
4. **Motion.** Dopo l'ok, l'orchestrator passa il brief motion a SA6B. I render tornano in `<project>/motion/<scena>/renders/`.
5. **Plan e rifinitura.** `cuts.json` → `plan.py` → `edit.json`. Caption: solo refusi, mai riformulare. B-roll, overlay, motion come shot, split screen con `"y": 960` sulle caption, musica ~12 dB sotto la voce. La somma dei `dur` = `duration`.
6. **Preview + QA.** `build.py --preview`, poi `check_frames.py --step 0.25` e `verify_final.py`. Guarda tutti i fogli (zone UI in rosso). Correggi i difetti bloccanti e ri-builda. I check si eseguono, non si dichiarano.
7. **🚦 GATE 2 — preview.** Ritorna path della preview + verdetto QA (PASSA / NON PASSA con difetti a tempo). Note dell'utente una alla volta su `edit.json`.
8. **Finale ed export.** `build.py` → 1080x1920 H.264 High 30 fps bt709, AAC 48 kHz, −14 LUFS, `+faststart`, più `captions.srt`. 4:5 e 16:9 riformattati dal finale (crop sul volto, caption alla nuova y), mai schiacciati. `verify_final.py` sul finale.
9. **🚦 GATE localizzazione (se richiesta).** Lingue, modalità (dubbing + sottotitoli HeyGen / dubbing pulito + caption del brand / solo sottotitoli), numero di persone che parlano, termini da non tradurre, durata libera o fissa, revisione sottotitoli, **consenso alla voce clonata**, stima crediti. Master pulito senza caption. HeyGen `mode: precision`. Per le ads: revisione dell'SRT tradotto prima del render. In modalità "caption del brand": il doppiato rientra in 72, nuova trascrizione whisper, caption e motion rifatte nella lingua target. QA completo per ogni lingua.
10. **Consegna.** Upload Drive, manifest, versioni precedenti tenute con nome parlante.

## Best practice (dettaglio nei reference di 72)
- **Ritmo:** short-form un cambio visivo ogni 3-4 s (massimo 5); long-form ~5 s, grafiche solo dove spiegano. Il cambio più leggero che funziona: zoom → b-roll → screenshot → parola chiave → numero/grafico → b-roll animato → effetti.
- **Hook:** primi 2 s in faccia, mai coperti. Attacco dritto sulla prima parola.
- **Audio:** highpass 80 Hz → denoise → de-esser → compressore 3:1 → loudnorm −14 LUFS / −1,5 dBTP. Micro-fade 8/12 ms su ogni taglio. Voce ovattata: catena `open`.
- **Caption:** parole dette, 2-4 per chunk, bianche con ombra, y 1420 (960 nello split), fuori dalle zone UI. Sempre anche l'SRT.
- **Safe zone 9:16:** alto 220 px, basso 400 px, destra 130 px. YouTube: angolo in basso a destra libero negli ultimi 20 s.
- **iPhone HDR:** convertito in SDR bt709; al primo progetto controlla i colori.
- **Schermate vere**, mai ricostruite. **Musica** solo con licenza commerciale.
- **Reference outlier** quando si vuole battere un formato: mosse viste in 2+ video, mai stimare le view.

## Regole
1. Due gate di montaggio (tagli e piano, preview) più il gate di localizzazione. Mai render finale né traduzione a pagamento senza ok.
2. Caption = parole dette. Testo aggiunto a schermo = copy SA7, verbatim.
3. Numeri a schermo solo da fonte.
4. Consenso scritto per volti e voci di terzi, e per ogni voce clonata in HeyGen.
5. Mai API key in chat, log o repo: `.env` non committato o keychain della CLI.
6. I claim tradotti restano i claim approvati: una lingua che chiede un claim diverso torna a SA7.
7. Non modificare i file delle skill installate: gli adattamenti stanno in `72`, `73`, `74`.

## Output strutturato → `final/assets/` + manifest

```
## VIDEO MONTATI
Concept 1: [Nome] — formato F[1-5] · durata
- [ ] 9:16 finale  · QA: PASSA [data] · LUFS · pause max
- [ ] 4:5 / 16:9 se richiesti
- [ ] captions.srt
- Motion SA6B usate: [scene]
- Lingue: [it ✓ · en-US (dub + caption brand, precision, revisionato da …) · es-MX …]
- Drive link: [url]
```

Naming: `{brand}_{campaign}_{concept}_{format}_{variant}[_{lang}].mp4`.

## Handoff
- Finali + SRT + manifest → **Orchestrator** (`final/assets/`), poi `51_meta_build` per il lancio.
- Feedback sullo stile → registro di `context/brand/video_style.md`. Errori tecnici e limiti nuovi (HeyGen, ffmpeg, whisper) → `directives/feedback_log.md`.
