#!/bin/bash
# Aggiorna le skill esterne dalle repo ufficiali (lanciare dalla root del repo del team).
set -euo pipefail
npx skills add heygen-com/hyperframes -a claude-code -y            # hyperframes*, motion-graphics, talking-head-recut, embedded-captions, slideshow…
npx skills add Barty-Bart/motion-graphics -a claude-code -y        # motion-broll, object-separation
npx skills add greensock/gsap-skills -a claude-code -y             # gsap-*
npx skills add emilkowalski/skills -a claude-code -y               # animate, emil-design-eng, review-animations, improve-animations…
npx skills add https://github.com/heygen-com/skills --skill heygen-translate -a claude-code -y
# Facoltativo, alternativa React a HyperFrames (repo senza licenza dichiarata: si installa, non si ridistribuisce)
# npx skills add remotion-dev/skills -a claude-code -y
npx hyperframes telemetry disable || true
echo "Controlla con git diff che nessuna skill abbia un nome in conflitto con quelle del team."
