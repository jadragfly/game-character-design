# Layout guide images

These PNGs are attached to every row generation as a layout-only reference. They tell Seedream how to compose the output:

- `<row>__auto.png` — the auto-mode layout: 8 separate cells side-by-side, telling the model "produce 8 distinct frames".
- `<row>__grid.png` — the grid-mode fallback layout: a 4-column-by-2-row grid.

The pet must NOT inherit any pixels from these guides. The guide is invisible scaffolding. Treat any output that includes guide colors, borders, or text as failed.

If the guides are missing or you want to regenerate them, run:

```bash
python scripts/build_layout_guides.py
```
