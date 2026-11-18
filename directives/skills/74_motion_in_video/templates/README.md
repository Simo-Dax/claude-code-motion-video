# Template motion — stile "keynote"

Tre scene di partenza per i cutaway animati dentro un video parlato. Testate in produzione su reel verticali: si copiano, si cambiano testi, tempi e colori, si renderizzano in ~15 s.

| Cartella | Mossa | Durata | Quando |
|---|---|---|---|
| `scene-titolo/` | tre sfere 3D arrivano dalla profondità, titolo da sfocato a nitido, camera che si avvicina | 1.74 s | nome di un prodotto, di un concetto, di una notizia |
| `scene-lista-spunte/` | card in vetro inclinate in 3D che si raddrizzano; ogni riga si avvicina e si spunta sulla parola detta | 4.10 s | elenchi, requisiti, piani, pro/contro, step |
| `scene-iphone-cta/` | iPhone disegnato in codice ruota verso la camera, tap su "Segui" | 2.80 s | CTA finale (segui, iscriviti, scarica) |

## Lo stile

- **Profondità vera:** `perspective: 1400-1800px`, oggetti in `preserve-3d` che arrivano da lontano (`z: -500…-900`), inclinati 20-50°, e si raddrizzano verso la camera. Durante l'hold ruotano di pochi gradi: la scena non è mai ferma.
- **Vetro:** card con gradiente bianco 16% → 4%, bordo bianco 22%, riflesso in alto, ombra lunga sotto.
- **Camera:** dolly-in leggero (scala 1.12 → 1) su tutta la durata.
- **Movimento:** ingressi `expo.out` 0.5-0.75 s, titoli da sfocato a nitido (`blur 16-18px → 0`). Molla leggera (`back.out(1.4-2)`) solo sulle conferme. Stagger 0.08-0.1 s.
- **Una parola per scena** con il gradiente sul testo.

## Palette: da sostituire con quella del brand

I template escono con una palette demo (blu e giallo su fondo quasi nero). Sostituisci gli hex con i ruoli di `context/brand/motion.md`:

| Ruolo | Demo | Sostituisci con |
|---|---|---|
| Fondo | `#01060f` | fondo scuro del brand (mai bianco dentro un video con caption bianche) |
| Luci di fondo | `#2C6FC4`, `#103B72` | colore primario del brand e una sua variante scura |
| Accento / conferma | `#FABD00` (simbolo `#031026`) | accento del brand |
| Gradiente parola chiave | `#6fa3ea → #FABD00` | primario chiaro → accento |
| Testo | `#f5f5f7` titoli, `#86868b` secondario | invariati, o i grigi del brand |

## Come si usa

```bash
cp -R directives/skills/74_motion_in_video/templates/scene-titolo <project>/motion/<scena>
mkdir -p <project>/motion/<scena>/fonts
cp <font del brand>.ttf <project>/motion/<scena>/fonts/brand.ttf    # licenza commerciale. Senza font del brand: Inter
```

Nel file `index.html`:
1. `data-duration` (root e `.clip`) = durata del cutaway sul timeline del video.
2. Testi = parole dette o copy approvato al gate. Mai claim o numeri non detti.
3. Tempi delle azioni (spunta, tap) = tempo della parola detta − inizio del cutaway.
4. Colori dalla tabella sopra.
5. `npx hyperframes check` → `npx hyperframes render --output renders/video.mp4` (fuori dal sandbox).

Per lo split screen: canvas 1080x960, contenuto tra y=240 e 900.

Regole HyperFrames: niente `.html` di backup nella stessa cartella (errore `multiple_root_compositions`), `window.__timelines["main"]` registrato alla fine del callback `document.fonts.ready`.
