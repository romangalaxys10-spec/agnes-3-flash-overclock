# Unslop UI, by phase

Same rules as `prompts/unslop-ui-untested.txt` and `docs/unslop.md`, split so a router can hand out one phase. Experimental, untested on Agnes; opinionated taste rules, not measured facts.

## Phase: direction

Lock ONE taste direction, justified by the product, before any styling. Write one sentence of physical scene (who, where, what light, what mood) to decide light versus dark; never default. Pick a colour commitment deliberately: restrained (neutrals plus one accent), committed, full palette, or drenched. Name palette roles: bg, surface, ink, muted, accent, border. Pair type on a contrast axis or use one family in several weights. Mark unknown brand facts [NEEDS INPUT]; do not invent them.

## Phase: audit

Inventory slop tells in ONE viewport per pass, with quoted evidence (class names, colours, layout moves) and severity critical, high or medium. Fix critical and high before adding craft. Run `python3 unslop_check.py <src>` and add the manual items from `docs/unslop.md` that text scanning cannot see. Also list 3 to 5 things to keep; do not rewrite for sport.

## Phase: polish

Work on static hierarchy, type, colour and layout against the locked direction. Prefer deleting decoration to adding it; remove at least one decorative element per pass. Body text at least 4.5:1 contrast (large text 3:1). Body line length 65 to 75ch. Display size at most 6rem and tracking no tighter than -0.04em. Cards only when they are the best affordance; no nested cards, no identical repeated grids, no 01/02/03 markers unless the content is a real sequence, no radius of 24px or more on cards and inputs, no 1px border plus a wide soft shadow on one element, no z-index soup.

## Phase: motion

Only after static polish. Remove decorative loops first. Animate transform and opacity, not layout properties; use exponential ease-out, never bounce or elastic. One orchestrated moment beats scattered micro-animations. Never scale an image on hover; animate the card's background, border or shadow instead. Give every animation a prefers-reduced-motion alternative, and never gate content visibility on a script-added class.

## Phase: persist

Record standing taste rules in DESIGN.md (tokens, bans, decisions) and link it from AGENTS.md so the next session cannot reintroduce the slop.
