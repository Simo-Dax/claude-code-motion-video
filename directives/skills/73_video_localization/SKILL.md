<!-- Copyright (c) 2026 Simone Dassereto. All rights reserved. See LICENSE. -->
# 73 — Video Localization (dubbing e sottotitoli in altre lingue con HeyGen)

**Agente:** SA6C (Video Editing) · **Comando:** `/pm-localize`
**Input:** video finito da `72_video_editing` (o da SA6/SA6B) + lingue target + `captions.srt` originale se c'è
**Output:** `output/<brand>/25_Video_Edits/<slug>/_out/loc/<lingua>/` (MP4 doppiato, SRT tradotto, note di revisione)
**Motore:** HeyGen Video Translation, via **MCP ufficiale** (OAuth, crediti del piano) o **CLI/API** (API key). La skill operativa è `heygen-translate` in `.claude/skills/heygen-translate/` (ufficiale HeyGen, MIT): questa skill decide **cosa** chiedere e **come rientra nel montaggio**, quella sa **come** chiamare HeyGen.

---

## Cosa fa

Prende un video già approvato nella lingua originale e lo porta in un'altra lingua: stessa persona in camera, voce clonata nella lingua target, labbra risincronizzate, sottotitoli opzionali. Due modalità di uscita:

| Modalità | Cosa esce | Quando |
|---|---|---|
| **Dubbing + sottotitoli HeyGen** | video doppiato con caption già bruciate | test, volumi alti, mercati secondari |
| **Dubbing senza sottotitoli** | video doppiato pulito; caption rifatte da 72 nello stile del brand | ads e contenuti di brand: caption e grafiche coerenti con il design system |
| **Solo sottotitoli** | SRT tradotto, nessun dubbing | quando la voce originale deve restare (founder, testimonial veri). Non serve HeyGen: Claude traduce `captions.srt` mantenendo i tempi (stessi blocchi, max 2 righe da 24 caratteri), revisione come allo Step 4, poi 72 brucia le caption tradotte o si caricano come caption native |

---

## Setup (una volta per workspace)

| Passo | Come | Note |
|---|---|---|
| MCP HeyGen | `claude mcp add --transport http heygen https://mcp.heygen.com/mcp/v1/` (oppure il blocco in `.mcp.json`, vedi sotto) | Login OAuth al primo uso, niente API key. Consuma i crediti del piano HeyGen. Tool `mcp__heygen__*` |
| CLI HeyGen (consigliata) | install da docs HeyGen, poi `heygen auth login` con la API key da https://app.heygen.com/settings?nav=API | Serve per la revisione dei sottotitoli (proofread) e per le richieste multi-lingua: oggi non sono nell'MCP |
| Skill | `.claude/skills/heygen-translate/` (già nel pacchetto) | Rileva da sola MCP o CLI. Se c'è `HEYGEN_API_KEY` nell'ambiente usa la CLI |

```json
{"mcpServers": {"heygen": {"type": "http", "url": "https://mcp.heygen.com/mcp/v1/"}}}
```

Mai la API key in chat, nei log o nel repo: va in `.env` (non committato) o nel keychain della CLI.

---

## Step 1 — 🚦 GATE brief di localizzazione

Chiedi solo quello che manca, una o due domande per volta:
1. **Lingue target** (anche varianti regionali: "Spagnolo (Messico)"). Valida con `list_video_translation_languages`.
2. **Modalità**: dubbing + sottotitoli HeyGen, dubbing pulito + caption del brand, o solo sottotitoli.
3. **Persone che parlano** nel video (`speaker_num`). Il numero sbagliato scambia le voci a metà video.
4. **Termini da non tradurre**: nome brand, prodotti, claim registrati. HeyGen non accetta un glossario fisso: si sistemano in revisione.
5. **Durata**: libera (`enable_dynamic_duration: true`, suona più naturale) o identica all'originale (`false`, obbligatoria se le motion devono restare sincronizzate senza rifarle).
6. **Revisione dei sottotitoli prima del render?** Default sì per ads, contenuti di brand, video oltre 3 minuti, settori regolati.
7. **Consenso**: la persona in camera ha autorizzato la clonazione della voce per questo uso? Senza consenso scritto non si parte.

Stima i crediti (minuti × lingue × modalità; saldo con `get_current_user`) e **aspetta l'ok** prima di lanciare.

## Step 2 — Master da tradurre

| Modalità | Master |
|---|---|
| Dubbing + sottotitoli HeyGen | rebuild da 72 **senza caption** (`"captions": []` in una copia di `edit.json`, `_out/master_clean.mp4`) e senza testi a schermo nella lingua originale se possibile. Altrimenti le caption originali restano sotto quelle nuove |
| Dubbing pulito + caption del brand | stesso master pulito |
| Solo sottotitoli | il finale va bene così com'è, serve l'SRT originale |

Musica: se il video ha musica sotto la voce, meglio un master con voce sola e musica a parte (`disable_music_track: true` altrimenti), poi la musica si rimette in 72.

Upload: link pubblico al file, oppure upload locale (`upload_asset` da MCP o `heygen asset create --file`), **massimo 32 MB**. Sopra, comprimi (`ffmpeg -crf 26`) o usa un link.

## Step 3 — Parametri per profilo

| Profilo | Parametri |
|---|---|
| Talking head / founder / UGC (default) | `mode: precision`, `enable_speech_enhancement: true`, `enable_caption: true\|false` (secondo la modalità), `enable_dynamic_duration: true`, `keep_the_same_format: true` |
| Voiceover su b-roll, podcast | `mode: precision`, `translate_audio_only: true`, `enable_speech_enhancement: true` |
| Musica forte sotto la voce | come talking head + `disable_music_track: true` |
| Brand con voce registrata in HeyGen | talking head + `brand_voice_id` |
| Bozza veloce per decidere | `mode: speed` (più rapido, lip-sync meno fedele) |

Strumenti MCP: `create_video_translation` (una lingua per richiesta), `get_video_translation` (stato e `video_url`), `list_video_translations`. Multi-lingua in un colpo e proofread: CLI `heygen video-translate create` / `heygen video-translate proofreads …`. Stato ogni 30-60 s, in background, senza riempire la chat.

## Step 4 — Revisione dei sottotitoli (proofread, consigliata per le ads)

1. Crea la sessione di proofread (CLI), scarica l'SRT tradotto e quello originale.
2. Correggi: nomi di brand e prodotti, claim (devono restare quelli approvati da SA7 e da `creative_claims_compliance`), registro (tu/lei), numeri e valute, unità di misura.
3. Per le lingue che il team non legge: revisione di un madrelingua o almeno back-translation in italiano per controllare il senso.
4. Ricarica l'SRT corretto e genera il video finale.

## Step 5 — Rientro nel montaggio (modalità "caption del brand")

1. Scarica il video doppiato in `_out/loc/<lingua>/dubbed.mp4`.
2. Nuovo progetto 72 con il doppiato in `clips/`: `ingest.py --lang <codice>` trascrive l'audio tradotto con i tempi parola per parola.
3. `plan.py` → caption nella lingua target con lo stile del brand; correggi i refusi usando l'SRT revisionato come riferimento, mai riformulare.
4. **Motion e testi a schermo**: se la durata è cambiata o le grafiche contengono testo in lingua originale, chiedi a SA6B di rifarle con i testi tradotti (copy approvato) e i nuovi tempi parola. Se `enable_dynamic_duration: false`, i tempi restano e basta cambiare i testi.
5. Musica rimessa a −12 dB sotto la voce, export, QA completo di 72.

## Step 6 — QA e consegna

- QA di `72` (`references/qa.md`) su ogni lingua: formato, LUFS, safe zone, caption leggibili.
- In più: lip-sync guardato a 1x sui primi 5 s e sulle frasi con più movimento; nomi di brand pronunciati bene; nessuna parola nella lingua originale rimasta nelle caption o nelle grafiche.
- Naming: `{brand}_{campaign}_{concept}_{format}_{variant}_{lang}.mp4` (es. `acme_LeadGen_C1_9x16_A_es-MX.mp4`).
- Handoff a `final/assets/` con una riga per lingua nel manifest (modalità, mode HeyGen, revisionato sì/no, revisore).

---

## Regole

1. Mai lanciare traduzioni senza ok sui crediti stimati.
2. Consenso scritto della persona per la voce clonata, per ogni uso e mercato.
3. I claim tradotti restano i claim approvati: se in una lingua serve un claim diverso, torna a SA7.
4. Non si traducono video con testi a schermo nella lingua originale senza un piano per quei testi (rifarli o accettarli consapevolmente).
5. Errori o limiti nuovi (lingue con lip-sync debole, file troppo grandi, tempi) → `directives/feedback_log.md`.
