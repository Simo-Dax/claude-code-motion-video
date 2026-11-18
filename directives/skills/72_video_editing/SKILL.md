<!-- Copyright (c) 2026 Simone Dassereto. All rights reserved. See LICENSE. -->
# 72 — Video Editing (montaggio da girato → MP4 pronto per l'ads o l'organico)

**Agente:** SA6C (Video Editing) · **Comando:** `/pm-video-edit`
**Input:** girato del cliente o del creator (clip in camera, voiceover, screenshot) + `note.md` · oppure un video già renderizzato da SA6 (`62`, `58`, `61`) o da SA6B da vestire con caption e grafiche
**Output:** `output/<brand>/25_Video_Edits/<YYYY-MM-DD>-<slug>/_out/` (MP4 finale + `captions.srt` + versioni precedenti con nome parlante)
**Motore:** script Python in `scripts/` (ffmpeg + whisper.cpp + Pillow), tutto locale, zero crediti.

---

## Cosa fa (e cosa non fa)

Monta materiale **già girato**: tagli, pulizia audio, b-roll, overlay di screenshot, motion graphics inserite come shot, caption, export per piattaforma. Non scrive lo script (quello è `55_video_script`), non genera video con l'AI (quello è SA6: `62`, `25`, `59`…), non disegna le motion graphics (quello è SA6B: le riceve come render e le monta).

| Serve… | Dove |
|---|---|
| Montare clip girate: tagli, silenzi, b-roll, caption, export | **72 (questa)** |
| Solo caption su un video già finito, stile locked | `63_auto_captions` (più veloce). Se servono anche tagli o grafiche → 72 |
| Card, titoli, lower-third sopra un parlato senza rimontarlo | skill HyperFrames `talking-head-recut` |
| Grafica animata da inserire (hook, numero, lista, split) | SA6B → `74_motion_in_video` / `67_motion_design`, poi torna qui come shot |
| Versione in altre lingue (dubbing, sottotitoli) | `73_video_localization`, dopo il finale |

---

## Prerequisiti (una volta per macchina)

- **macOS** (la conversione HDR usa VideoToolbox), **ffmpeg** (`brew install ffmpeg`), **whisper.cpp** (`brew install whisper-cpp`), **Python 3 + Pillow** (`pip3 install pillow`).
- Modello whisper: `~/.cache/whisper/ggml-large-v3-turbo-q5_0.bin` (scaricalo da Hugging Face `ggerganov/whisper.cpp`). Altro modello: env `REEL_WHISPER_MODEL`.
- Font delle caption: env `VIDEO_FONT` (path .ttf/.ttc del font del brand) e `VIDEO_FONT_INDEX` (indice del peso nel .ttc). Default: Helvetica Neue Bold di sistema.
- Questa build di ffmpeg può non avere `libass`/`drawtext`: le caption sono **PNG generati con Pillow e sovrapposti**. Non usare `subtitles=` o `drawtext=`.

## Contesto da leggere prima

1. `context/brand/video_style.md` (caption, ritmo, audio, safe zone del brand). Se manca, crealo da `context/brand/video_style.template.md` con l'utente (Step 0).
2. `context/brand/motion.md` e `design_system.md` (colori, font).
3. `note.md` del progetto e, se c'è, il concept SA5 e il copy SA7 da cui nasce il video.
4. `references/formats.md`, `references/edit_json.md`, `references/playbook.md`, `references/qa.md` di questa skill.

---

## Step 0 — Video style del brand (una volta per brand)

Compila `context/brand/video_style.md` partendo dal template: font e peso delle caption, posizione, ombra, parole per caption, profilo di ritmo (short-form o long-form), catena audio, musica, cosa è vietato. Ogni feedback dell'utente che vale per tutti i video finisce nel **registro** in fondo al file, con la data.

## Step 1 — Cartella e ingest

```bash
directives/skills/72_video_editing/scripts/new_project.sh <brand> <slug>
# l'utente mette i file in clips/ voiceover/ overlays/ music/ e compila note.md
python3 directives/skills/72_video_editing/scripts/ingest.py <project_dir> --lang it
```

Scrive in `_work/`: `probe.json` (durata, rotazione, HDR, audio), `sheets/*.jpg` (contact sheet con timestamp), `words/*.json` (parole whisper con tempi), `transcript.md` (ogni parola con il suo id `[n]`). **Guarda** i contact sheet e leggi transcript e note: ora sai cosa c'è in ogni clip.

Clip HDR (iPhone): l'ingest e il build le convertono in SDR bt709. Al primo progetto con HDR controlla i colori della preview (pelle, cieli). Se sono slavati, chiedi di rigirare con HDR spento.

## Step 2 — 🚦 GATE 1: formato, tagli, piano visivo

Proponi all'utente, in un solo messaggio:
- **formato** (F1-F5, `references/formats.md`) con il perché;
- **transcript con i tagli** visibili (~~barrato~~ quello che togli). Default: si tengono tutte le parole, si tagliano respiro iniziale, coda e silenzi; le parole solo se c'è un errore vero (falsa partenza, frase sbagliata e ridetta: tieni l'ultima versione). Ogni taglio di parola si propone uno per uno;
- **refusi di trascrizione** su nomi propri, brand, termini tecnici (si correggono nelle caption, non si riformula);
- **cut list e mappa visiva**: quale b-roll, screenshot o motion va sopra quale frase, con i tempi. Senza volto in camera (F4) la mappa è obbligatoria;
- **brief per SA6B** se servono motion graphics (testo esatto, tempo della parola, formato 1080x1920 o 1080x960 per lo split);
- durata stimata e formati di export.

**Aspetta l'ok.** Poi scrivi `_work/cuts.json`:

```json
{"takes": [{"src": "clips/IMG_0012.MOV", "drop": [0, 1, "40-47"]},
           {"src": "voiceover/vo.m4a", "from": 0, "to": 212, "drop": [3]}],
 "max_pause": 0.5}
```

**Silenzi veri:** whisper incolla le parole e sposta i loro tempi dentro le pause. Prima del piano misura i silenzi sull'audio (`ffmpeg -af silencedetect=n=-35dB:d=0.25`, oppure RMS < −34 dB per ≥ 0,5 s) e allinea `t0`/`t1` delle parole ai bordi dei silenzi in `_work/words/*.json` (backup `.orig.json`). Lascia 0,1 s di aria per lato. L'attacco: guarda l'inviluppo dei primi 2 s e sposta `t0` della prima parola dove parte davvero la voce.

## Step 3 — Plan

```bash
python3 directives/skills/72_video_editing/scripts/plan.py <project_dir>
```

Scrive `edit.json`: `spine` (segmenti audio tenuti), `captions` (chunk di 2-4 parole sulla timeline finale), `shots` (parlato in camera già in sync, zoom 1.0/1.08 alternato a ogni jump cut), `overlays: []`.

## Step 4 — Rifinitura di `edit.json`

Schema completo in `references/edit_json.md`. In breve:
- **Caption:** correggi solo i refusi. Mai riformulare: la caption è quello che la persona dice.
- **B-roll:** spezza lo shot parlato in due e metti il b-roll in mezzo, con `in` del secondo pezzo avanzato della durata del b-roll. La somma dei `dur` = `duration`.
- **Motion graphics (da SA6B):** shot `{"src": "motion/<slug>/renders/video.mp4", "in": 0, "dur": 2.5}`. I render stanno in `motion/`, **mai in `clips/`** (l'ingest li trascriverebbe).
- **Split screen (F3):** shot di faccia con `"split": {"top": "motion/<slug>/renders/video.mp4", "in": 0}`, `"fy": 0.55`, e `"y": 960` su ogni caption che tocca il tratto.
- **Screenshot sopra la faccia:** `overlays` `{file, t0, t1, width, y}`. App e schermate vere, mai ricostruite.
- **Musica:** `"music": {"file": "music/x.mp3", "db": -22}`, poi misura: circa 12 dB sotto la voce.
- **Audio registrato lontano o ovattato:** `"audio_chain": "open"`.

## Step 5 — Preview, QA, 🚦 GATE 2

```bash
python3 directives/skills/72_video_editing/scripts/build.py <project_dir> --preview
python3 directives/skills/72_video_editing/scripts/check_frames.py <project_dir> _out/preview.mp4 --step 0.25 [--compare best.mp4] [--region top]
python3 directives/skills/72_video_editing/scripts/verify_final.py <project_dir> _out/preview.mp4
```

Guarda **tutti** i fogli di `_work/check/` (zone UI di Instagram in rosso) e leggi `verify.json`. Correggi i difetti bloccanti, ri-builda, poi mostra all'utente il path della preview con il verdetto del QA (tabella in `references/qa.md`). I check si **eseguono**, non si dichiarano. **Aspetta l'ok o le note**, applicale una alla volta su `edit.json`, ri-builda.

## Step 6 — Finale ed export

```bash
python3 directives/skills/72_video_editing/scripts/build.py <project_dir>
python3 directives/skills/72_video_editing/scripts/verify_final.py <project_dir> --no-words   # se tra preview e finale è cambiato solo l'encode
```

`_out/<slug>.mp4`: 1080x1920, H.264 High, 30 fps, yuv420p bt709 tv-range, AAC 48 kHz, −14 LUFS, `+faststart`. Più `_out/captions.srt` (per le caption native di piattaforma o per la localizzazione). Le versioni precedenti restano in `_out/` con nome parlante (`v1-solo-caption`, `v2-con-motion`).

Altri formati: `build.py` oggi esporta solo 9:16. Per 4:5 (1080x1350) e 16:9 (1920x1080) si riformatta con ffmpeg dal finale (crop con `fy` del volto, caption rifatte alla nuova y) oppure si chiede all'utente se estendere lo script. Mai un 9:16 schiacciato in 4:5.

## Step 7 — Handoff

- File finale + SRT + manifest → `final/assets/` dell'orchestrator, naming `{brand}_{campaign}_{concept}_{format}_{variant}.mp4`.
- Se `note.md` chiede altre lingue → `73_video_localization` sul finale (o sul master pulito, vedi lì).
- Feedback dell'utente: stile → registro di `context/brand/video_style.md`; errori tecnici → `directives/feedback_log.md`.

---

## Regole

1. Due gate: tagli e piano visivo, poi preview. Mai render finale senza ok.
2. Le caption sono le parole dette. Testo aggiunto a schermo (hook, CTA) = copy: viene da SA7 o passa da `49_anti_ai_slop`.
3. Numeri a schermo solo da fonte (brief, SA3, VOC, dashboard). Senza fonte non si mettono.
4. Musica solo con licenza d'uso commerciale. Volti e voci di terzi solo con consenso.
5. Disco: `build.py` si ferma sotto 2 GB liberi e avvisa sotto 5. Sotto 5 GB i render vanno uno alla volta e `_work/build/shots/` si cancella dopo il finale.
6. Se qualcosa si rompe: `pip3 install pillow` se manca Pillow; Puppeteer/Chrome mancanti per HyperFrames → `npx puppeteer browsers install chrome`; render HyperFrames in timeout dentro un sandbox → lancialo fuori dal sandbox.
