# Unslop UI filters (experimental)

A set of anti-"generic AI design" checks for UI and frontend output, in three forms: a prompt, a static checker, and a manual review list that the QA panel uses.

## Provenance and honesty

The rules come from a personal skill ("unslop-ui") that the repo owner's assistant distilled on 2026-09-29 from the prompts and skills published on aiuxplayground.com (Unslop my UI, Polish frontend UI, Polish UI motion, Impeccable, Frontend Design). They are paraphrased and condensed, not copied verbatim, and the upstream licenses were not checked for this repo, so no upstream text is vendored here. These are opinionated taste rules, not measured facts: no study here shows they raise quality. Not tested with Agnes.

## Parts

| Path | What |
| --- | --- |
| `prompts/unslop-ui-untested.txt` | The 5-step process and ban list as a prompt |
| `agnes_kit/unslop.py`, `unslop_check.py` | Offline static scanner for CSS, HTML, JSX/TSX, Vue, Svelte text |
| `unslop/examples/` | `sloppy.css` (synthetic, trips most rules) and `clean.css` (trips none) |
| `docs/unslop-phases.md` | The same rules split by phase, for the router |
| `tests/test_unslop.py` | Tests for the scanner |

## Scanner

```bash
python3 unslop_check.py path/to/src            # text report
python3 unslop_check.py styles.css --json
python3 unslop_check.py src --fail-on critical # default fail level is high
```

Exit 0: nothing at or above `--fail-on`. Exit 1: findings. Exit 2: error or no scannable files. It skips `node_modules`, `.git`, `dist`, `build`, `third_party`.

Detected (regex over text; false positives and misses are expected):

| Severity | Rules |
| --- | --- |
| critical | gradient text; side-stripe border over 1px |
| high | Inter/Roboto/Arial/system-ui first in font-family; purple or indigo gradient; border-radius 24px+ (not pill); ghost card (1px border + blur 16px+); bounce or overshooting easing; image scaled on hover; hex-vs-hex text contrast under 4.5:1 |
| medium | backdrop-filter blur; z-index 999+; letter-spacing below -0.04em; clamp() display size above 6rem; tiny tracked uppercase label; animation with no reduced-motion alternative in the file; Tailwind equivalents of several of the above |

Not detectable by text, so manual (the optional `ui-slop` QA lens applies this list):
- body background in the default warm cream/sand "premium" move, or near-black plus one acid accent as an unconsidered default theme
- identical card grids, nested cards, numbered 01/02/03 markers with no real sequence, an eyebrow above every section
- broadsheet hairlines and zero radius used as decoration
- text overflowing its container at any breakpoint (test at every viewport)
- contrast against images, gradients or computed styles
- whether the direction was chosen from the product, and whether anything decorative was removed

Contrast uses only same-rule hex `color` and `background`; anything else is unchecked. A clean scan is not a pass.

## With the QA panel and proof gate

The optional `ui-slop` lens in `qa-panel/optional-lenses.json` (enable with `qa_panel.py render --with-optional`; it is a 26th reviewer, not part of the original 25) runs `unslop_check.py` on any UI code and applies the manual list above, reporting results as normal findings. For delivery, a UI task can attach the scanner output and screenshots as artifacts in an Anti Helizzinator proof envelope; the visual proof gate checks that inspection is asserted, not that it is true.

## Not included

No MCP tool or `check.py` constraint wraps the scanner yet (the router tool `agnes_route` can serve the rules). Text-writing slop (filler phrases, inflated vocabulary) is not covered by this feature.
