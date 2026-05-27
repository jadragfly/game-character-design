# Examples

四个端到端示例覆盖常见场景。每个示例假设 **Seedream 4.5（火山引擎 Volcano Engine）** 的凭证已配置：

```bash
export DOUBAO_API_KEY="your-doubao-api-key"
export DOUBAO_API_URL="https://ark.cn-beijing.volces.com"
```

## 1. 纯文本概念（原创角色）

用户说："给我做一只小蓝色机器人宠物，叫 Boltie，额头上有一个黄色 LED。"

```bash
python scripts/prepare_run.py \
  --pet-name "Boltie" \
  --description "A tiny blue robot pet with a single yellow LED on its forehead." \
  --style original \
  --category "Original Characters" \
  --output-dir ./run/boltie

python scripts/generate_base.py --run-dir ./run/boltie

# 检查 decoded/base.png 是 Boltie 应有的形象后：
python scripts/generate_row.py --run-dir ./run/boltie --row idle
python scripts/generate_row.py --run-dir ./run/boltie --row waving
python scripts/generate_row.py --run-dir ./run/boltie --row running-right
python scripts/derive_running_left.py --run-dir ./run/boltie     # Boltie 对称，可镜像
python scripts/generate_row.py --run-dir ./run/boltie --row waiting
python scripts/generate_row.py --run-dir ./run/boltie --row review
python scripts/generate_row.py --run-dir ./run/boltie --row jumping
python scripts/generate_row.py --run-dir ./run/boltie --row failed
python scripts/generate_row.py --run-dir ./run/boltie --row happy

python scripts/extract_frames.py --run-dir ./run/boltie
python scripts/chroma_key.py     --run-dir ./run/boltie
python scripts/compose_atlas.py  --run-dir ./run/boltie
python scripts/package_pet.py    --run-dir ./run/boltie --slug boltie--yourname
python scripts/render_qa.py      --run-dir ./run/boltie
```

产物：`run/boltie/final/pet.json` 和 `run/boltie/final/spritesheet.webp`。

## 2. 参考图（真实柯基照片）

用户上传 `~/Downloads/my-corgi.jpg`：

```bash
python scripts/prepare_run.py \
  --pet-name "Corgo" \
  --description "Stylized chibi corgi based on user's pet photo." \
  --style animal \
  --category Animals \
  --reference ~/Downloads/my-corgi.jpg \
  --output-dir ./run/corgo

python scripts/generate_base.py --run-dir ./run/corgo
```

base 会把照片简化成同色系的 chibi 柯基。base 通过后：

```bash
python scripts/generate_row.py --run-dir ./run/corgo --row all
# Corgo 胸部毛色不对称——不能镜像。--row all 会正常生成 running-left。

python scripts/extract_frames.py --run-dir ./run/corgo
python scripts/chroma_key.py     --run-dir ./run/corgo
python scripts/compose_atlas.py  --run-dir ./run/corgo
python scripts/package_pet.py    --run-dir ./run/corgo --slug corgo--yourname
python scripts/render_qa.py      --run-dir ./run/corgo
```

提示：参考图带有不对称花纹（单边色块、单耳下垂等）时，跳过 `derive_running_left.py`，让 `generate_row.py --row all` 正常生成 running-left。

## 3. 动漫角色

用户说："做一只初音未来的 Codex pet。"

```bash
python scripts/prepare_run.py \
  --pet-name "Miku" \
  --description "Chibi Hatsune Miku with twin teal pigtails." \
  --style anime \
  --category "Anime Characters" \
  --output-dir ./run/miku

python scripts/generate_base.py --run-dir ./run/miku
```

`anime` 风格预设负责简化——产物应是像素 chibi Miku，不是动漫 keyart。如果 base 看起来太精修，重跑这一步。

```bash
python scripts/generate_row.py --run-dir ./run/miku --row all

# Miku 双马尾对称，但领带是单边的——不要镜像。
# --row all 会自然生成 running-left。

python scripts/extract_frames.py --run-dir ./run/miku
python scripts/chroma_key.py     --run-dir ./run/miku
python scripts/compose_atlas.py  --run-dir ./run/miku
python scripts/package_pet.py    --run-dir ./run/miku --slug miku--yourname
python scripts/render_qa.py      --run-dir ./run/miku
```

## 4. 修复流程

QA 显示 `failed.png` 旁边漂着一个红色大 X（禁用）。只修这一行：

```bash
# 用 --force 覆盖之前的 decoded 输出，单独重跑：
python scripts/generate_row.py --run-dir ./run/miku --row failed --force

# 只重新切帧 + 抠图这一行：
python scripts/extract_frames.py --run-dir ./run/miku --row failed
python scripts/chroma_key.py     --run-dir ./run/miku --row failed

# 然后重新合成图集 + 重新打包：
python scripts/compose_atlas.py  --run-dir ./run/miku
python scripts/package_pet.py    --run-dir ./run/miku --slug miku--yourname
python scripts/render_qa.py      --run-dir ./run/miku
```

## 5. 回退到 grid 模式

如果某行 auto 模式持续返回 6 帧或 10 帧，对该行切换到 grid 模式：

```bash
python scripts/generate_row.py --run-dir ./run/miku --row jumping --mode grid --force
python scripts/extract_frames.py --run-dir ./run/miku --row jumping
python scripts/chroma_key.py     --run-dir ./run/miku --row jumping
python scripts/compose_atlas.py  --run-dir ./run/miku
```

`--mode grid` 会切换 prompt，并使用 `aspect_ratio: 16:9` + `sequential_image_generation: "disabled"`。生成的是一张 4 列 × 2 行的网格图，由切帧脚本本地切片。

## 6. 没有 API key 时的 smoke test

在配 `DOUBAO_API_KEY` 之前可以先空跑流水线：

```bash
export SEEDREAM_MOCK_EN=true

python scripts/prepare_run.py --pet-name Test --description "test" --style codex-pixel --category Animals --output-dir ./run/test
python scripts/generate_base.py --run-dir ./run/test
python scripts/generate_row.py --run-dir ./run/test --row all
python scripts/extract_frames.py --run-dir ./run/test
python scripts/chroma_key.py     --run-dir ./run/test
python scripts/compose_atlas.py  --run-dir ./run/test
python scripts/package_pet.py    --run-dir ./run/test --slug test--mock
python scripts/render_qa.py      --run-dir ./run/test
```

产出的 spritesheet 由占位图拼成——几何与打包链路完整可验证，只是视觉是占位。
