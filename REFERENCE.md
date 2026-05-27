# Reference

`pet-design` 技能的详细参考。SKILL.md 没说清楚的地方查这里。

## 1. Codex Pet 文件格式

最终的宠物是一个文件夹里的两个文件：

```
pets/<pet-slug>--<author-slug>/
├── pet.json
└── spritesheet.webp
```

`pet.json` schema：

```json
{
  "id": "<pet-slug>--<author-slug>",
  "displayName": "Codex",
  "description": "A friendly orange cat companion.",
  "spritesheetPath": "spritesheet.webp"
}
```

`id` 必须等于文件夹名。`spritesheetPath` 是相对该文件夹的路径。

## 2. Atlas 布局

```
1536 x 1872，8 列 x 9 行，单帧 192 x 208

      col0   col1   col2   col3   col4   col5   col6   col7
row0  idle           ...                                   (frame 0..7)
row1  waving         ...
row2  running-right  ...
row3  running-left   ...
row4  waiting        ...
row5  review         ...
row6  jumping        ...
row7  failed         ...
row8  happy          ...
```

行序固定，不可改动。一行内未用到的 cell 保持完全透明。每行的 frame 0 是最左侧 cell。

## 3. Seedream 4.5 API（火山引擎 Volcano Engine）

技能调用部署在火山引擎的 Seedream 4.5，通过豆包图像生成端点。

端点：`${DOUBAO_API_URL}/api/v3/images/generations`，**同步**返回。

请求：

```http
POST /api/v3/images/generations HTTP/1.1
Authorization: Bearer ${DOUBAO_API_KEY}
Content-Type: application/json

{
  "model": "doubao-seedream-4-5-251128",
  "prompt": "...",
  "image": ["data:image/png;base64,...", "data:image/png;base64,..."],
  "size": "4096x4096",
  "sequential_image_generation": "auto",
  "watermark": false
}
```

字段规则：

- `model`：当 `DOUBAO_API_URL` 命中已知豆包入口前缀时为 `doubao-seedream-4-5-251128`，否则为 `seedream-4-5-251128`。客户端自动识别，无需手填。
- `image`：0–14 项。每项是公网 `http(s)://` URL 或 `data:image/...;base64,...` data URI。本地文件由 `seedream_client.py` 自动转为 data URI。
- `size`：像素串。aspect ratio → 像素映射：

  | aspect_ratio | size          |
  |--------------|---------------|
  | `1:1`        | `4096x4096`   |
  | `4:3`        | `3840x2880`   |
  | `3:4`        | `2880x3840`   |
  | `16:9`       | `3840x2160`   |
  | `9:16`       | `2160x3840`   |
  | `3:2`        | `3840x2560`   |
  | `2:3`        | `2560x3840`   |
  | `21:9`       | `3840x1646`   |

- `sequential_image_generation`：`"auto"`（模型自行决定生成 1..N 张相关图）或 `"disabled"`（单图）。
- `watermark`：始终 `false`。

响应：

```json
{
  "model": "doubao-seedream-4-5-251128",
  "created": 1700000000,
  "data": [
    { "url": "https://.../seedream4-xxx.jpg", "size": "4096x4096" }
  ],
  "usage": { "generated_images": 1, "output_tokens": 10, "total_tokens": 10 }
}
```

`seedream_client.py` 把每个 `data[].url` 下载到 `<out_dir>/<job-id>__<i>.png`，返回本地路径列表。

## 4. 两条生成路径

```
主路径（sequential auto）              回退路径（单张网格）
┌────────────────────────────┐       ┌────────────────────────────┐
│ image: [base, layout-guide]│       │ image: [base, layout-grid] │
│ size:  1:1 (4096x4096)     │       │ size:  16:9 (3840x2160)    │
│ seq:   "auto"              │       │ seq:   "disabled"          │
│ prompt: 8 frames as 8      │       │ prompt: 4x2 grid layout    │
│         separate images    │       │                            │
└────────────────────────────┘       └────────────────────────────┘
        │                                    │
        ▼                                    ▼
  8 张独立的帧 jpg                      1 张网格 jpg → 本地切片
        │                                    │
        └────────────┬───────────────────────┘
                     ▼
            extract_frames.py
            → 8 张 192x208 PNG（仍带 chroma-key 背景）
                     │
                     ▼
              chroma_key.py
            → 8 张透明 PNG
```

通过 `generate_row.py --mode auto|grid` 选择路径（默认 `auto`）。当 `auto` 返回的帧数不正确时，脚本会发出警告，用户可改用 `--mode grid` 重跑。

## 5. Prompt 工程

每个 base prompt 由四块拼成：

1. **Style block** — 完全照搬 `prompts/style/<style>.txt`
2. **Subject block** — 宠物描述、特征、配色、道具
3. **Background block** — `solid #00FF00 chroma-key background, no other colors, no shadows, no scenery`
4. **Forbidden block** — 完全照搬 `prompts/base/_forbidden.txt`

每个 row prompt 由六块拼成：

1. **Layout block** — 帧数与排列（auto：`8 separate images, each frame a clean centered pose`；grid：`4 columns x 2 rows grid, each cell isolated`）
2. **Identity lock** — "keep the exact same character from reference image 1; same head, face, palette, prop, outline weight, silhouette"
3. **Action block** — 来自 `prompts/rows/<row>.txt`，定义 8 帧分镜
4. **Style block** — 与 base 同
5. **Background block** — 与 base 同
6. **Forbidden block** — `prompts/rows/_forbidden.txt`（在 base forbidden 基础上扩展行特定禁用项）

拼好的 prompt 落到 `<run-dir>/prompts/<job-id>.txt`，便于用户检查实际发出去的内容。

## 6. 风格预设

| Style key       | 何时使用 |
|-----------------|---------|
| `codex-pixel`   | 默认。匹配内置 Codex pet 风格——像素 chibi。 |
| `anime`         | 参考图是动漫 / 游戏角色。在保留特征的前提下简化为 chibi。 |
| `animal`        | 参考图是真实或风格化动物。产出柔和的 chibi 动物。 |
| `original`      | 没有明显参照风格的原创角色。chibi 基底，配色由描述决定。 |

四个风格强制相同的 chibi 比例、描边规则、禁用清单，区别只在面部、眼睛、比例的描述语言。

## 7. jobs.json 清单

`prepare_run.py` 写入 `<run-dir>/jobs.json`：

```json
{
  "pet_name": "Codex",
  "slug": "codex",
  "description": "A friendly orange cat companion.",
  "style": "codex-pixel",
  "category": "Animals",
  "chroma_key": "#00FF00",
  "user_references": ["/abs/path/to/ref.png"],
  "jobs": {
    "base":          { "status": "pending", "mode": "auto", "decoded": null },
    "idle":          { "status": "pending", "mode": "auto", "decoded": null },
    "waving":        { "status": "pending", "mode": "auto", "decoded": null },
    "running-right": { "status": "pending", "mode": "auto", "decoded": null },
    "running-left":  { "status": "pending", "mode": "auto", "decoded": null, "derive_from_mirror": false },
    "waiting":       { "status": "pending", "mode": "auto", "decoded": null },
    "review":        { "status": "pending", "mode": "auto", "decoded": null },
    "jumping":       { "status": "pending", "mode": "auto", "decoded": null },
    "failed":        { "status": "pending", "mode": "auto", "decoded": null },
    "happy":         { "status": "pending", "mode": "auto", "decoded": null }
  }
}
```

状态：`pending` → `succeeded` | `failed` | `mirrored`。每个脚本读、改、原子写回该文件。不支持并发编辑——按顺序串行运行脚本。

## 8. Chroma-Key 抠图

默认 chroma key 是 `#00FF00`。`chroma_key.py` 把 HSV 空间内距离 chroma key 在容差内的像素设为透明，再做一遍 1-pixel 去毛刺以清理轮廓边缘的残留。容差存放在 `<run-dir>/jobs.json` 的 `chroma_tolerance`（默认 30，范围 0–60）。如果 API 输出有轻微绿色泄漏，调高；如果宠物本体颜色被吃掉，调低。

宠物本体不能使用接近 `#00FF00` 的饱和绿色（毛色、道具、点缀都不行）。base prompt 已经显式禁止。

## 9. `seedream_client.py` 错误码

| Code | 含义 |
|------|------|
| `E_NO_KEY`     | `DOUBAO_API_KEY` 未设置且 mock 关闭。配置 key。 |
| `E_NO_URL`     | `DOUBAO_API_URL` 未设置。配置 base URL。 |
| `E_HTTP_<n>`   | Seedream 返回非 2xx，`n` 是状态码。 |
| `E_DOWNLOAD`   | 无法把 `data[].url` 下载到本地。 |
| `E_FRAME_COUNT`| `auto` 模式返回的帧数不是 8。建议改 `--mode grid`。 |

错误会写入 `<run-dir>/jobs.json` 的 `jobs.<row>.error`，并打印到 stderr。

## 10. Mock 模式

设 `SEEDREAM_MOCK_EN=true`。客户端在本地合成一张占位图（不走网络）并返回成功。这让用户可以：

- 在拿到 API key 之前先把整条流水线跑通验证可用性
- 修改代码后空跑 smoke test，不消耗 credits

`NODE_ENV=production` 时 mock 模式自动失效（避免在生产环境误触发）。
