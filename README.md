<!-- Copyright (c) 2026 Simone Dassereto. All rights reserved. See LICENSE. -->
# Motion & Video Kit per Claude Code

Due subagent per Claude Code che producono **motion graphics in codice** e **video montati**, con tutte le skill che richiamano: montaggio da girato, caption, export, QA misurato e localizzazione in altre lingue con HeyGen (dubbing con lip-sync, con o senza sottotitoli). Tutto locale e gratuito, tranne HeyGen.

Sono progettati per un performance marketing agent a subagent (SA1 ricerca competitor … SA6 asset statici, SA7 copy, SA8 analytics, SA9 CRM), dove si affiancano a SA6 come **SA6B** e **SA6C**. Funzionano anche in qualsiasi progetto Claude Code: le skill native `72`, `73`, `74` si usano da sole.

| Agente | Fa | Skill native | Skill esterne |
|---|---|---|---|
| **SA6B** `sa6b-motion-graphics` | motion graphics in codice: ad motion autonome e grafiche dentro un video parlato | `67_motion_design` (già nel repo), **`74_motion_in_video`** | HyperFrames (già nel repo), `motion-broll`, `object-separation`, `gsap-*`, `animate`, `emil-design-eng`, `review-animations`, `improve-animations` |
| **SA6C** `sa6c-video-editing` | montaggio da girato, caption, export, QA, localizzazione HeyGen | **`72_video_editing`**, **`73_video_localization`**, `63_auto_captions` (già nel repo) | `heygen-translate`, `talking-head-recut` e `embedded-captions` (già nel repo) |

## Cosa c'è dentro

```
.claude/agents/
  sa6b_motion_graphics.md         istruzioni del subagent motion
  sa6c_video_editing.md           istruzioni del subagent video editing
.claude/commands/
  pm-motion-video.md  pm-video-edit.md  pm-localize.md
.claude/skills/                   skill esterne (MIT), ognuna con il suo LICENSE
  motion-broll  object-separation  gsap-core  gsap-timeline  gsap-performance
  animate  emil-design-eng  review-animations  improve-animations  heygen-translate
directives/skills/
  72_video_editing/               SOP montaggio + scripts/ (ingest, plan, build, check_frames, verify_final, new_project.sh)
                                  + references/ (formats, edit_json, playbook, qa) + templates/video_project/
  73_video_localization/          SOP dubbing e sottotitoli con HeyGen (MCP o API)
  74_motion_in_video/             SOP motion dentro i video + templates/ (titolo 3D, lista con spunte, CTA telefono)
context/brand/
  video_style.template.md         da compilare una volta per brand
install.sh                        copia tutto nel repo e controlla i tool
update_skills.sh                  riprende le ultime versioni delle skill esterne
INTEGRAZIONE.md                   le modifiche a mano a claude.md, SA6, 14, SA5, COMMANDS.md
THIRD_PARTY_LICENSES.md
LICENSE
```

## Installazione

```bash
git clone https://github.com/Simo-Dax/claude-code-motion-video.git && cd claude-code-motion-video
./install.sh /percorso/al/tuo/progetto
```

Poi le 5 modifiche di `INTEGRAZIONE.md`, il setup della macchina (ffmpeg, whisper, HeyGen) e i 4 test di verifica. Le skill esterne già presenti nel repo non vengono sovrascritte.

## Requisiti

macOS, ffmpeg, whisper.cpp con il modello `ggml-large-v3-turbo-q5_0`, Python 3 con Pillow, Node.js, Chrome (per HyperFrames). HeyGen: un piano attivo, collegato via MCP (OAuth) o API key. Tutto il resto è locale e gratuito: solo HeyGen consuma crediti.

`install.sh` si aspetta un progetto con `claude.md` e `.claude/agents/`. In un progetto diverso copia a mano le cartelle `.claude/` e `directives/skills/` e salta `INTEGRAZIONE.md`.

## Licenza

© 2026 **Simone Dassereto**. Uso personale e per il tuo brand o la tua azienda consentito, lasciando intatti `LICENSE` e le intestazioni. Vietati senza permesso scritto: ridistribuzione, rivendita, inserimento in corsi o prodotti, rimozione del nome dell'autore, uso per addestrare modelli. Le skill di terze parti in `.claude/skills/` restano sotto la loro licenza MIT ([`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md)).
