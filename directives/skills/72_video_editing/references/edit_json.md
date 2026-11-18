# `edit.json` — schema

`plan.py` lo scrive, Claude lo rifinisce, `build.py` lo renderizza. È testo: ogni modifica del montaggio è una modifica qui.

```json
{
  "duration": 42.6,
  "spine":    [{"src": "clips/IMG_0012.MOV", "in": 0.42, "out": 6.10}],
  "captions": [{"t0": 0.0, "t1": 0.9, "text": "Tre errori che"}],
  "shots":    [{"src": "clips/IMG_0012.MOV", "in": 0.42, "dur": 5.68, "zoom": 1.0}],
  "overlays": [],
  "music":    {"file": "music/track.mp3", "db": -22},
  "grade":    "eq=contrast=1.04:saturation=1.05",
  "caption_y": 1420,
  "caption_shadow": "deep",
  "audio_cleanup": true,
  "audio_chain": "open"
}
```

## Chiavi globali

| Chiave | Default | Cosa fa |
|---|---|---|
| `duration` | da `plan.py` | durata finale = somma dello spine. La somma dei `dur` degli shot deve coincidere (tolleranza 0,05 s, altrimenti il build si ferma) |
| `spine` | da `plan.py` | segmenti audio tenuti, in ordine. Micro-fade 8/12 ms su ogni taglio: niente click |
| `music` | nessuna | `file` + `db` (gain della musica). Parti da −22 e misura: musica ~12 dB sotto la voce. Fade out di 1,5 s in coda |
| `grade` | nessuno | filtro ffmpeg applicato alle riprese, mai ai render in `motion/` |
| `caption_y` | 1420 | centro verticale delle caption full-frame |
| `caption_shadow` | morbida | `"deep"` = ombra di contatto + alone largo, per caption sopra immagini chiare |
| `audio_cleanup` | true | `false` = solo loudnorm (voiceover già masterizzato) |
| `audio_chain` | standard | `"open"` = denoise leggero + EQ di presenza, per voce registrata lontano o ovattata. Oppure una catena ffmpeg completa |

## `shots` (traccia video)

| Chiave | Esempio | Note |
|---|---|---|
| `src` | `clips/IMG_0012.MOV`, `motion/hook/renders/video.mp4`, `overlays/foto.png` | video, render motion o immagine (crop 9:16) |
| `in` | 14.2 | secondo di partenza nella sorgente |
| `dur` | 2.5 | durata sullo timeline finale |
| `zoom` | 1.08 | punch-in. Alterna 1.0 / 1.08 a ogni jump cut |
| `fy` | 0.3 | ancora verticale dello zoom (0 = alto, 0.5 = centro). ~0.3 tiene il volto in campo sui punch-in |
| `push` | 0.025 | zoom extra lungo lo shot (dolly-in lento) |
| `split` | `{"top": "motion/s1/renders/video.mp4", "in": 0, "ratio": 0.5}` | split screen F3: grafica sopra, faccia sotto. `top` può essere `.mp4` o immagine. `ratio` = frazione di altezza della grafica (sopra 0.55 la faccia diventa un francobollo) |

## `captions`

`t0`, `t1`, `text` sulla timeline finale. Opzionali per singola caption: `y` (es. 960 alla giuntura dello split), `size` (default 62). Chunk da 2-4 parole, massimo 24 caratteri per riga.

## `overlays` (screenshot sopra la faccia)

`{"file": "overlays/dashboard.png", "t0": 3.2, "t1": 6.0, "width": 0.8, "y": 760}`: card con angoli arrotondati e ombra morbida, larga `width` × 1080, centrata su `y`.
