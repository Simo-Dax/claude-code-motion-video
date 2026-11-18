<!-- Copyright (c) 2026 Simone Dassereto. All rights reserved. See LICENSE. -->
# 74 — Motion in Video (grafiche animate dentro un video parlato)

**Agente:** SA6B (Motion Graphics) · **Comando:** `/pm-motion-video`
**Input:** progetto di `72_video_editing` dopo il GATE 1 (transcript con i tempi, cut list, brief motion) · `context/brand/motion.md`
**Output:** `output/<brand>/25_Video_Edits/<slug>/motion/<scena>/renders/video.mp4` (o `.mov` con alpha), pronti per entrare in `edit.json` come shot o come metà alta dello split
**Motori:** HyperFrames (template di questa skill, `/motion-graphics`), `/motion-broll` (UI e processi a tempo con le parole), `/object-separation` (soggetto scontornato). Locali, zero crediti.

---

## Quando questa e quando `67_motion_design`

| Serve… | Skill |
|---|---|
| Motion **autonoma** (ad motion, launch promo, kinetic type, stat, loop, pagina web → MP4) | `67_motion_design` |
| Motion **dentro un video parlato**: hook animato, cutaway su una parola, lista che si spunta, split screen, CTA finale, b-roll animato sincronizzato alla voce | **74 (questa)** |

La differenza: qui ogni azione deve cadere sulla parola detta, il formato dipende dal layout del montaggio (1080x1920 full-frame o 1080x960 per lo split) e le caption di 72 scorrono sopra.

---

## Regole di stile dentro un video (valgono se `context/brand/motion.md` non dice altro)

- **Fondo scuro** dentro un video verticale: le caption sono bianche e su fondo chiaro spariscono. Eccezione: metà alta dello split (le caption stanno alla giuntura).
- Contenuto tra **y=250 e y=1350** su 1080x1920. Nello split, tra y=240 e y=900 del canvas 1080x960. 130 px liberi a destra (pulsanti di Instagram).
- **Massimo ~1/3 della durata** coperto da cutaway full-frame. 2-4 cutaway per 30 s. Il resto è la faccia.
- **Mai** sui primi 2 s (l'hook si regge sul volto) né su frasi personali o di opinione.
- **Ogni azione cade sulla parola detta**: spunta, tap, numero che parte, parola che si illumina. Tempo = tempo della parola sul timeline finale − inizio del cutaway. È la cosa che rende il cutaway vivo.
- **Una sola parola evidenziata** per scena. Titoli corti (1-3 parole, l'etichetta del passaggio), righe con le parole dette.
- Ingressi 0,3-0,5 s ease-out, stagger 0,08-0,1 s tra elementi gemelli, niente rimbalzi evidenti. Un oggetto che cambia forma vale più di una dissolvenza.
- Buoni candidati: nome di un prodotto o concetto, elenchi e requisiti, numeri, confronti, CTA finale.
- Numeri solo se detti nel video o approvati da fonte. Schermate vere, mai ridisegnate: se manca lo screenshot, card grigia "SCREENSHOT DA FORNIRE: <cosa>" finché non arriva.

## Step 0 — Brand motion system

Se `context/brand/motion.md` non esiste, lo crea `67_motion_design` Step 0. Da lì prendi: palette (fondo, testo, accento, luci), font (con licenza commerciale: file in `fonts/brand.ttf` della scena), durate e curve. Lo stile "keynote" dei template (fondo quasi nero, luci sfocate, oggetti in profondità, gradiente su una parola) è il default se il brand non ha uno stile motion: si adatta ai colori del brand, la forma resta.

## Step 1 — Brief motion (dentro il 🚦 GATE 1 di 72)

Per ogni scena, una riga:

| # | Tempo (finale) | Parola d'aggancio | Layout | Motore | Testo a schermo (esatto) | Durata |
|---|---|---|---|---|---|---|
| 1 | 2.1-4.0 | "tre errori" | cutaway 1080x1920 | template `scene-titolo` | "3 errori" | 1.9 s |
| 2 | 8.4-20.6 | "primo…secondo…terzo" | split 1080x960 | template `scene-lista-spunte` | titolo + 3 righe | 12.2 s |

Motore per tipo:

| Contenuto | Motore |
|---|---|
| Titolo, nome prodotto, concetto | template `scene-titolo` |
| Lista, requisiti, step, piani, pro/contro | template `scene-lista-spunte` |
| CTA finale (segui, scarica, visita) | template `scene-iphone-cta` |
| Hook in kinetic type, numero, grafico | `/motion-graphics` (`kinetic-type`, `stat`, `charts`) |
| UI, tool, cursore che clicca, processo, confronto timed sulle parole | `/motion-broll` |
| Testo dietro la persona, sfondo sostituito | `/object-separation` + composizione HyperFrames sopra/sotto la maschera |

Il testo a schermo è copy: viene dal parlato o da SA7, passa da `49_anti_ai_slop` se aggiunto. **Aspetta l'ok** insieme ai tagli di 72.

## Step 2 — Tempi parola sul timeline finale

I tempi in `_work/words/` sono sulla sorgente. Per avere i tempi sul montaggio: build della preview di 72 senza motion, poi `whisper-cli` sulla preview (stesso modello di `ingest.py`) e usa quei tempi. Per YouTube: SRT del montaggio o whisper sul file finale. Mai stimare dai sottotitoli se c'è di meglio.

## Step 3 — Costruzione

**Template (HyperFrames):**

```bash
cp -R directives/skills/74_motion_in_video/templates/scene-titolo <project>/motion/<scena>
mkdir -p <project>/motion/<scena>/fonts && cp <font del brand>.ttf <project>/motion/<scena>/fonts/brand.ttf
```

Nel file `index.html`: `data-duration` (root e `.clip`) = durata della scena; testi approvati; tempi delle azioni = tempo parola − inizio scena; colori sostituiti con quelli di `motion.md` (vedi `templates/README.md`). Per lo split: canvas 1080x960.

**`/motion-broll`** (adattamenti, senza modificare la skill):
- non chiedere stile e palette: rispondi da `motion.md`. Chiedi solo video, densità e cosa evitare;
- niente accent arancio della skill: lo stato attivo si segna con contrasto e peso, o con l'accento del brand;
- font del brand al posto di Geist (Geist Mono resta per codice e terminale);
- verticale: `M.scene({W:1080, H:1920, …})`, `center:[540,960]`, contenuto tra y=250 e 1350; split: `H:960`;
- solo cutaway full-frame `.mp4` dentro un verticale. I pannelli `bg:null` più piccoli del frame vanno resi a 1080x1920 nella posizione giusta;
- vocabolario d'interazione (pill+click, progress, check, card, slider, toggle, tabs, chart+tooltip, terminale, confronto): etichette solo dal parlato.

**`/object-separation`:** prima del primo uso chiedi (torch ~1-2 GB + modello SAM 2, ~323 MB su Apple Silicon). venv in `.tmp/`. Prova su ~20 frame prima del range intero. Le maschere si riusano.

**`/motion-graphics`:** formato e palette dal brief, fondo scuro, testo sopra y=1350.

## Step 4 — Check e preview (🚦 GATE 2 di 72)

```bash
cd <project>/motion/<scena>
npx hyperframes check
npx hyperframes render --output renders/video.mp4          # opaco
npx hyperframes render --format mov --output renders/video.mov   # con alpha, solo full-frame 1080x1920
```

Guarda 2 frame per scena (inizio e fine) prima di montare. Poi gli shot entrano in `edit.json` (vedi `72_video_editing/references/edit_json.md`):

```json
{"src": "motion/titolo/renders/video.mp4", "in": 0, "dur": 1.9}
{"src": "clips/IMG_0012.MOV", "in": 14.2, "dur": 12.2, "fy": 0.55, "split": {"top": "motion/lista/renders/video.mp4", "in": 0}}
```

I render stanno in `motion/`, mai in `clips/`. L'audio resta la voce: `build.py` prende solo il video dagli shot. La preview complessiva e il QA li fa 72.

## Regole HyperFrames da ricordare

- Un solo `.html` root per cartella: niente backup accanto (errore `multiple_root_compositions`).
- `window.__timelines["main"]` registrato alla fine del callback `document.fonts.ready`, timeline `paused: true`, deterministica.
- Render fuori dal sandbox se Chrome va in timeout.
- **Mai** `npx hyperframes feedback`, `publish`, `cloud`, `lambda` o `--file-issue`: mandano dati fuori. Telemetria spenta: `npx hyperframes telemetry disable`.

## Registro

Feedback dell'utente sullo stile → registro in fondo a `context/brand/motion.md` con la data. Errori tecnici → `directives/feedback_log.md`.
