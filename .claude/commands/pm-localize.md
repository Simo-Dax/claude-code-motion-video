---
description: Localizza un video finito in altre lingue con HeyGen (MCP o API) — dubbing con voce clonata e lip-sync, con o senza sottotitoli, o solo sottotitoli tradotti. Skill nativa 73_video_localization (SA6C).
argument-hint: [video o cartella progetto] [lingue, es. en-US es-MX] [modalità: dub+sub / dub+caption brand / solo sub]
---

# /pm-localize — Video Localization

Esegui la skill nativa **`directives/skills/73_video_localization/SKILL.md`** (SA6C — Video Editing), con la skill operativa `.claude/skills/heygen-translate`.

Argomenti: $ARGUMENTS

## Cosa fare
1. Verifica il collegamento HeyGen: tool `mcp__heygen__*` o CLI `heygen auth status`. Se mancano, guida l'utente nel setup (SKILL.md, tabella Setup). Mai chiedere la API key in chat.
2. **🚦 GATE** lingue, modalità, persone che parlano, termini da non tradurre, durata, revisione, consenso alla voce clonata, **stima crediti** → OK utente.
3. Master pulito senza caption da `72`. Traduzione `mode: precision`, revisione SRT se ads o brand.
4. Modalità "caption del brand": il doppiato rientra in `72` (ingest nella lingua target, caption e motion rifatte).
5. QA per ogni lingua, naming con `_{lang}`, manifest.
