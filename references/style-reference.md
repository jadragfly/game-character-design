# Style Reference

The visual language every Codex pet must follow. Used both in prompts and during human review of the QA contact sheet.

## Proportions

- Head is 1.2x to 1.6x the width of the torso (chibi).
- Torso is short, often barely visible under the head.
- Limbs are tiny, sometimes just stubs.
- Total figure fits in the 192x208 cell with at least 12 px padding on every side.
- Eyes are large, simple shapes (dots, ovals, almond, or stylized closed-arc when smiling).

## Outline

- 1-2 px dark outline around every external silhouette and major internal shape.
- Outline color is a dark version of the body color (not pure black for light-colored pets).
- Inner detail lines are 1 px and only appear where structurally needed (mouth, nostril, prop edge).

## Palette

- 4-6 colors total per pet.
- One body color, one shade tone (darker), one highlight tone (lighter), one or two accent colors for prop/eyes/details.
- Avoid saturated greens close to `#00FF00` (they are removed by chroma keying).
- Use flat fills, not gradients. Cel shading only.

## Shading

- Single shadow tone, single highlight tone.
- Light implied from the upper-left.
- No gradients, no soft transitions, no antialiasing on the cel-shading boundaries.

## Allowed visual elements

- Body, head, limbs, tail, ears, hair, simple face (eyes + mouth).
- One signature prop (tool, hat, scarf, accessory) baked into the base portrait — must persist across all rows.
- Cel-shaded materials (matte color blocks).

## Forbidden visual elements

The complete forbidden list is in `prompts/base/_forbidden.txt` and `prompts/rows/_forbidden.txt`. The high-level summary:

- No 3D rendering, no realism, no painterly look, no anime keyart polish, no app-icon glossy treatment.
- No shadows, no glows, no auras, no particle effects.
- No motion lines, speed lines, action streaks, afterimages, or motion blur.
- No detached effects: floating sparkles, separated smoke, falling tears, floating symbols, exclamation marks.
- No text, labels, frame numbers, watermarks, UI panels.
- No background other than solid `#00FF00`.
- No saturated near-`#00FF00` greens on the pet itself.

## QA review checklist

When reviewing `qa/contact-sheet.png`:

- [ ] All 9 rows show the same pet (identity consistent)
- [ ] Same head shape, face, palette, outline weight across rows
- [ ] No row has a different prop or missing prop
- [ ] Each frame fits within its 192x208 cell (no clipping, no neighbor crossover)
- [ ] Background fully transparent everywhere except the pet body
- [ ] No forbidden detached effects in any frame
- [ ] Action reads correctly per row (idle subtle, jumping clearly vertical, running clearly horizontal cycle, etc.)
- [ ] `running-left` and `running-right` face opposite directions
- [ ] `failed` does not contain forbidden symbols (red X, FAIL text, etc.)
- [ ] `waving` does not contain motion arcs or sparkles
