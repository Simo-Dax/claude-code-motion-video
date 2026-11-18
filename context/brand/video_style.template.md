# Video style — <Brand>

Si compila una volta per brand (skill `72_video_editing` Step 0). Lo leggono SA6B e SA6C prima di ogni video. I valori sono numeri, non aggettivi.

## Caption
- Font: <path .ttf/.ttc> → env `VIDEO_FONT` (+ `VIDEO_FONT_INDEX` per il peso nel .ttc)
- Dimensione: 62 px su 1080x1920 · colore: bianco · ombra: morbida | deep
- Posizione: y 1420 (full-frame), y 960 (split)
- Parole per caption: 2-4 · max 24 caratteri per riga
- Cosa evitare: <es. emoji, parole evidenziate a colori, MAIUSCOLO>

## Ritmo
- Profilo: short-form (cambio ogni 3-4 s) | long-form (~5 s)
- Silenzi tagliati sopra: 0,5 s
- Copertura massima motion full-frame: 1/3 della durata
- Formati preferiti: F1 / F2 / F3 / F4 / F5 (references/formats.md)

## Audio
- Catena voce: standard | open
- Loudness: −14 LUFS
- Musica: <libreria con licenza> · ~12 dB sotto la voce

## Grading
- `grade`: <filtro ffmpeg, es. eq=contrast=1.04:saturation=1.05> | nessuno

## Export
- Formati: 9:16 1080x1920 · 4:5 1080x1350 · 16:9 1920x1080
- Lingue: <it, en, es…> (skill 73)

## Registro feedback
Una riga per feedback che vale per tutti i video: data, cosa, regola.
- AAAA-MM-GG · 
