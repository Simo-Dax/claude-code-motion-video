# Playbook di montaggio (euristiche, non checklist)

Mosse che funzionano spesso. Usale quando il video le chiede, saltale quando no, e al GATE 1 di' quali hai scelto e perché. Sui conflitti vince `context/brand/video_style.md`.

## Il cambio visivo più leggero che funziona

Si sale di livello solo se il contenuto lo giustifica:

1. **Punch-in / zoom** sul parlato (1.0 → 1.08, alternato ai jump cut). Costo zero, regge da solo un video semplice.
2. **B-roll girato** sopra la frase che descrive.
3. **Overlay di uno screenshot vero** (card arrotondata), con la faccia ancora in campo.
4. **Parola chiave in kinetic type** (SA6B, `/motion-graphics`). Hook, frase da ricordare, una cifra.
5. **Numero o grafico animato** (SA6B, `stat` / `charts`). Numeri solo da fonte.
6. **UI, tool, processo, confronto a tempo con le parole** (SA6B, `/motion-broll`).
7. **Effetti speciali**: soggetto scontornato con testo dietro, trasformazioni (SA6B, `/object-separation`, `motion-effects`). Rari.

## Prima di montare

- **Reference outlier** (opzionale): 3-5 video dello stesso formato che hanno fatto almeno ~5x le view abituali del loro autore. Un frame al secondo + transcript: hook nei primi 3 s, secondi per grafica, parole al secondo, layout, caption, CTA. Una mossa vista in 2+ reference va in `moves.md` del progetto. Mai stimare le view.
- **`best.mp4`** (opzionale): il miglior video finora dello stesso profilo, metro per il ritmo (`check_frames.py --compare`).

## Tagli

- Default: **si tengono tutte le parole**. Si tagliano respiro iniziale, coda e silenzi **sopra 0,5 s**, misurati sull'audio e non sui tempi di whisper. 0,1 s di aria per lato.
- Niente tagli di intercalari o ripetizioni salvo errore vero o richiesta esplicita: il parlato naturale converte meglio di quello levigato.
- L'attacco parte dritto sulla prima parola.

## Grafica

- Mai cutaway sui primi 2 s (l'hook si regge sul volto) né su frasi personali o di opinione.
- Testo e grafica tra y=250 e y=1350 su 1080x1920: sotto ci sono le caption e la UI.
- App e schermate vere, mai ricostruite. Se serve un login per catturarle, chiedi.
- Ogni azione grafica cade sulla parola detta (tempi da `_work/words/`).

## Audio

- Catena voce standard: `highpass 80 Hz → afftdn (denoise) → deesser → compressore 3:1 → loudnorm −14 LUFS / −1,5 dBTP`. Micro-fade 8/12 ms su ogni taglio.
- Voce ovattata o registrata lontano: `"audio_chain": "open"` (meno denoise, taglio dei 330 Hz, presenza a 3,2 kHz, aria a 8 kHz).
- Musica circa 12 dB sotto la voce, fade out finale.
- Separare voce e musica da un audio già mixato: Demucs (`pip install demucs`, `demucs --two-stems=vocals file.wav`).

## Caption

- Parole dette, refusi corretti, mai riscritte. Chunk 2-4 parole, una o due righe, massimo 24 caratteri per riga.
- Bianche con ombra, centrate. Su fondi chiari `"caption_shadow": "deep"`, o meglio fondo scuro nelle motion.
- Sempre anche `captions.srt` in output: serve per le caption native di piattaforma e per la localizzazione.

## Feedback che diventano regole

Le note dell'utente si applicano una alla volta. Stile → registro di `context/brand/video_style.md`. Tecniche → `directives/feedback_log.md`. Lo scopo è che il montaggio successivo ne richieda meno.
