# Animation Rows

The 9 fixed action rows of a Codex pet, in atlas order top to bottom. Each row is 8 frames at 192x208 px each, played left to right.

| Row idx | Row id          | Loop kind         | When the host plays it |
|---------|-----------------|-------------------|------------------------|
| 0       | `idle`          | seamless loop     | Default state, nothing happening. |
| 1       | `waving`        | one-shot or loop  | First boot, hello, attention grab. |
| 2       | `running-right` | seamless loop     | Movement to the right. |
| 3       | `running-left`  | seamless loop     | Movement to the left. |
| 4       | `waiting`       | seamless loop     | Long-running task in progress (compile, build, fetch). |
| 5       | `review`        | seamless loop     | Reviewing diff or output. |
| 6       | `jumping`       | one-shot          | Notification, success small, "look at me". |
| 7       | `failed`        | one-shot then idle| Error, test failure, cancellation. |
| 8       | `happy`         | one-shot then idle| Build pass, test pass, deploy success. |

## Frame timing reference

The host renders frames at roughly 8–12 fps. So a single row is about 0.7–1.0 seconds. Each frame breakdown is designed for that speed: keep the motion physically plausible inside ~1 second.

## Row dialect

Each row has a per-row prompt under `prompts/rows/<row>.txt` that defines the 8-frame breakdown plus a row-specific forbidden list. The shared forbidden list is in `prompts/rows/_forbidden.txt`.

Detailed frame-by-frame language lives in those prompt files. Below is a quick sanity matrix.

| Row id        | Body must move? | Vertical change? | Side facing? | Special allowed effects |
|---------------|-----------------|------------------|--------------|--------------------------|
| idle          | minimal         | tiny breathing   | front        | none |
| waving        | one paw         | none             | front        | none |
| running-right | full cycle      | small bounce     | right        | none |
| running-left  | full cycle      | small bounce     | left         | none |
| waiting       | head tilts      | none             | front        | none |
| review        | lean + tilt     | small lean       | front        | none |
| jumping       | full body       | LARGE            | front        | none |
| failed        | slump           | small drop       | front        | one attached tear / smoke / star |
| happy         | hop + arms      | medium up        | front        | none (smile is enough) |

## running-left mirroring rule

`running-left` may be derived by horizontally flipping `running-right` if and only if all of the following are true:

- No side-specific markings (one-sided patch, single ear bow, etc.)
- No handed prop (a wand only in one paw, etc.)
- No readable text on the body
- No asymmetric lighting cue baked into the row
- No direction-specific pose semantic that breaks when flipped

If any of those is false, generate `running-left` normally. `derive_running_left.py` requires the user to confirm with `--confirm-appropriate-mirror` so this decision is explicit.
