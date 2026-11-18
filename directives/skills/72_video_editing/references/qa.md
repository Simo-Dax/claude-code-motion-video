# QA misurato (prima del GATE 2 e prima della consegna)

Si eseguono, non si dichiarano. Il verdetto va all'utente insieme alla preview: PASSA / NON PASSA, con ogni difetto a tempo e la correzione in termini di `edit.json`.

```bash
python3 directives/skills/72_video_editing/scripts/check_frames.py <project_dir> [video] --step 0.25 [--compare best.mp4] [--region top]
python3 directives/skills/72_video_editing/scripts/verify_final.py <project_dir> [video] [--max-pause 0.5] [--no-words]
```

`check_frames.py` scrive in `_work/check/` fogli con un frame ogni 0,25 s e le zone della UI di Instagram in rosso: **alto 220 px, basso 400 px, colonna pulsanti a destra 130 px**. Guardali tutti. `verify_final.py` scrive `_work/check/verify.json` ed esce con errore se cade un check duro.

| Check | Come | Passa se |
|---|---|---|
| Safe zone | fogli di `check_frames` | niente testo o grafica importante in zona rossa, tagliato al bordo o sovrapposto ad altro |
| Formato | `verify_final` → `format` | H.264, 1080x1920 (540x960 in preview), 30 fps, yuv420p, tv-range, AAC |
| Durata A/V | `av` | audio e video entro 0,05 s |
| Loudness | `lufs` | −14 LUFS ± 1 |
| Pause | `pauses` | nessun silenzio sopra 0,5 s rimasto |
| Parole | `words` (whisper sul finale vs parole tenute) | ≥ 90% uguali, nessuna parola mozzata o doppiata vera. Whisper sbaglia: le differenze si ascoltano prima di correggerle |
| Testo caption | `captions` (caption vs parole tenute) | nessuna parola persa (`plan.py` a volte perde le parole corte) |
| Caption a schermo | fogli | leggibili, mai sopra la bocca, in sync con la voce |
| Ritmo | `pace` (parole/s, riferimento short-form 3,1-3,8) + cambi di `check_frames` | short-form: un cambio ogni 3-4 s (F1, F2, F4), un beat ogni 2-3 s nello split. Un tratto statico oltre 5 s va giustificato |
| Finale | `ending` + ultimi frame | ultime parole intere, CTA leggibile; su YouTube l'angolo in basso a destra libero negli ultimi 20 s (end screen) |
| Beat test (se c'è `best.mp4`) | `--compare best.mp4` | cambi visivi e secondi al primo cambio non peggiori del riferimento. Se peggiori: aggiungi beat e rifai il render **una volta**, poi di' onestamente quale dei due è meglio |

Limite noto: gli ingressi morbidi (da sfocato a nitido) non superano la soglia di scena. Nello split i beat si contano dal piano della composizione, non dal contatore. Le zone rosse valgono per il verticale: per 16:9 ignorale.
