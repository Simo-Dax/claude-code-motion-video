# Formati video (si sceglie al GATE 1)

## Le quattro domande

1. La persona è in camera con una take buona? No → F4.
2. Spiega qualcosa che si vede (tool, schermata, processo, dati in fila)? Sì, per più di ~8 s → F3. Per un nome, un numero, una lista breve → F2.
3. È un'opinione, una storia personale, una frase forte? → F1 (la faccia regge).
4. Dura più di 40 s e mescola le cose sopra? → F5.

| Formato | Quando | Quando no | Layout | Ritmo | Caption |
|---|---|---|---|---|---|
| **F1 · Solo parlato** | frase forte, opinione, clip breve | spiegazioni lunghe senza niente da vedere | faccia piena, punch-in 1.0/1.08 a ogni taglio | un cambio ogni 3-4 s (gli zoom contano) | y 1420 |
| **F2 · Parlato + cutaway** | un nome, un numero, una lista breve, la CTA | spiegazione continua > ~8 s | faccia + 2-4 cutaway full-frame per 30 s, massimo ~1/3 della durata | un cambio ogni 3-4 s | y 1420, anche sopra i cutaway (fondo scuro) |
| **F3 · Split screen** | spiega un tool, schermate, processo, confronto, dati | opinioni e frasi personali; camera troppo vicina | grafica sopra (0-960), faccia sotto (960-1920) | un beat grafico ogni ~2-3 s nella metà alta | y 960, alla giuntura |
| **F4 · Voiceover su b-roll** | la persona non è in camera | c'è una take in camera buona | b-roll, overlay e motion a pieno schermo, mappa b-roll obbligatoria | un cambio ogni 2-4 s | y 1420 |
| **F5 · Ibrido** | sopra i 40 s: apertura in faccia, cuore spiegato, chiusura personale | sotto i 20 s | hook in faccia → split o cutaway sul tratto che spiega → faccia piena + CTA | come il formato di ogni tratto | come il tratto |

## Split screen (F3), geometria 1080x1920

| Zona | y | Regola |
|---|---|---|
| Grafica | 0-960 | composizione **1080x960**. I primi 220 px li copre la UI di Instagram: contenuto utile tra y 240 e 900. 130 px liberi a destra |
| Giuntura | ~960 | caption di 2-3 parole, una riga, `"y": 960` |
| Faccia | 960-1920 | occhi a ~1200-1300, bocca **sopra 1520**. iPhone a braccio: `"fy": 0.55` |

- Un solo shot di faccia per tutto il tratto split, niente jump cut con zoom alternato: il ritmo lo fa la grafica. Se il tratto ha tagli di silenzio, spezza lo shot ai bordi dello spine e passa a ogni pezzo la sua porzione di grafica (`split.in` avanzato).
- `"y": 960` su **ogni** caption che si sovrappone allo split, anche quelle iniziate un attimo prima.
- Una composizione SA6B per tratto, 1080x960, con più beat dentro, ognuno sulla sua parola. Mai una motion 1080x1920 nello split: viene tagliata al centro.

## Profili di ritmo

| | Short-form verticale (Reel, TikTok, Shorts, ads 9:16) | Long-form orizzontale (YouTube 16:9) |
|---|---|---|
| Obiettivo | fermare lo scroll, tenere fino alla fine | far capire, tenere fiducia per minuti |
| Ritmo visivo | un cambio ogni 3-4 s, massimo 5 | circa uno ogni 5 s, più lento nei ragionamenti |
| Motion | frequenti e brevi (1,5-3 s) | solo quando spiegano qualcosa, 4-7 al minuto in media |
| Hook | primi 2 s in faccia, mai coperti | primi 2 s in faccia |

Riadattare un long-form in short-form = rimontarlo con il ritmo short-form, non esportarlo e basta.
