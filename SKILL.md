---
name: game-character-design
description: 从概念或参考图设计游戏角色帧动画（1536x1872 spritesheet.webp + character.json），支持平台跳跃、格斗、动作冒险等游戏类型。通过 Seedream 4.5 图生图。用于设计游戏角色、主角、敌人、NPC 等动画。
---

# Game Character Design

## 概览

从概念、参考图（或两者都有）出发，制作游戏角色帧动画。技能产出 `1536x1872` 的 `spritesheet.webp` 加上 `character.json` 包。

同时支持 **宠物动画模式** (`--animation-mode pet`) 和 **游戏角色动画模式** (`--animation-mode game`)。

视觉生成委托给 **Seedream 4.5（火山引擎 Volcano Engine）**，通过豆包图像生成端点完成；切帧、抠图、图集合成、打包与 QA 由确定性的 Python 脚本完成。

## 起步配置（最先读）

技能通过一个 HTTP 端点调用 **Seedream 4.5（火山引擎）**。运行任何脚本前先配置两个环境变量：

```bash
export DOUBAO_API_KEY="your-doubao-api-key"
export DOUBAO_API_URL="https://ark.cn-beijing.volces.com"
```

可选的离线试跑模式（不真实调用 API，返回占位图，便于先把整条流水线跑通）：

```bash
export SEEDREAM_MOCK_EN=true
```

一次性安装 Python 依赖：

```bash
pip install -r requirements.txt
```

如果 `DOUBAO_API_KEY` 未设置且未开 mock，所有脚本都会立即报错并指回本节。

## 双模式支持

### 宠物动画模式 (`--animation-mode pet`)

| 项目 | 值 |
|------|----|
| 角色类型 | 桌宠、吉祥物、数字宠物 |
| 动作数 | 9 个（idle, waving, running-right, running-left, waiting, review, jumping, failed, happy） |
| 风格预设 | codex-pixel, anime, animal, original |

### 游戏角色动画模式 (`--animation-mode game`)

| 项目 | 值 |
|------|----|
| 角色类型 | 游戏主角、敌人、NPC、Boss |
| 动作数 | 完整版 11 个，精简版 7 个 |
| 风格预设 | platformer-16bit, platformer-indie, platformer-chibi, platformer-anime |

## 游戏角色动作速查

### 完整动作集（11 个，适合 RPG、格斗）

| 动作 | 说明 | 帧数 |
|------|------|------|
| idle | 待机站立 | 8 |
| walk-right | 向右行走 | 8 |
| walk-left | 向左行走 | 8 |
| jump | 跳跃上升 | 8 |
| fall | 下落 | 8 |
| crouch | 下蹲 | 4 |
| attack | 攻击/近战 | 6 |
| shoot | 射击/远程 | 6 |
| hit | 受击反应 | 6 |
| pickup | 拾取道具 | 6 |
| death | 死亡 | 6 |

### 平台跳跃精简集（7 个，适合超级马里奥类 + 射击游戏）

| 动作 | 说明 | 帧数 |
|------|------|------|
| idle | 待机站立 | 8 |
| walk-right | 向右行走 | 8 |
| walk-left | 向左行走 | 8 |
| jump | 跳跃 | 8 |
| crouch | 下蹲躲避 | 4 |
| attack | 攻击/射击（举枪射击动作） | 6 |
| pickup | 拾取道具 | 6 |

⚠️ **重要**：对于射击游戏，建议使用 `attack` 动画作为射击动作（角色举枪射击），而不是近战攻击。如果需要区分射击和近战，可以添加额外的 `shoot` 动作。

## Atlas 规格（通用）

| 项 | 值 |
|----|----|
| Atlas 尺寸 | `1536 x 1872` |
| 网格 | `8 列 x 9 行` |
| 单帧尺寸 | `192 x 208` |
| 格式 | PNG 或 WebP，透明 |
| Chroma Key | `#00FF00` |

## 默认工作流

### 宠物模式
```
1. 准备       →  prepare_run.py        (1 个 base 任务 + 9 个 row 任务)
2. base 图    →  generate_base.py      (canonical-base.png)
3. 9 行动作   →  generate_row.py       (identity 锁定的 9 行动作)
4. 收尾       →  extract → chroma_key → compose_atlas → package_pet → render_qa
```

### 游戏模式
```
1. 准备       →  prepare_run.py        (1 个 base 任务 + N 个 row 任务)
2. base 图    →  generate_base.py       (canonical-base.png)
3. 游戏动作   →  generate_row.py        (身份锁定的游戏动作)
4. 收尾       →  extract → chroma_key → compose_atlas → package_pet → render_qa
```

## 进度清单（游戏模式）

```
- [ ] 准备 <角色名> 的运行目录
- [ ] 想象 <角色名> 的主形象
- [ ] 描绘 <角色名> 的 N 套动作
- [ ] 生成 <角色名> 的帧动画
```

### 第 1 步：准备 run

**游戏角色示例（超级马里奥风格）：**
```bash
python scripts/prepare_run.py \
  --animation-mode game \
  --game-type platformer \
  --character-name "Super Red" \
  --description "A full body plumber hero character, complete figure from head to toe, wearing blue shirt, red cap, big mustache, standing pose, full view, no cut-off" \
  --style platformer-16bit \
  --category "Platform Games" \
  --output-dir ./run/super-red
```

**游戏角色示例（完整动作集）：**
```bash
python scripts/prepare_run.py \
  --animation-mode game \
  --game-type full \
  --character-name "Warrior Hero" \
  --description "A full body warrior character, complete figure from head to toe, muscular build, silver armor, flowing cape, determined expression, standing pose, full view, no cut-off" \
  --style platformer-anime \
  --category "Action Adventure" \
  --output-dir ./run/warrior-hero
```

**宠物模式示例：**
```bash
python scripts/prepare_run.py \
  --animation-mode pet \
  --character-name "Codex" \
  --description "A full body orange cat companion, complete figure from head to paw, sitting pose, full view, no cut-off" \
  --style codex-pixel \
  --category "Animals" \
  --output-dir ./run/codex
```

`--reference` 可选。不传时仅根据 `--description` + 风格 prompt 文本生图作为 base。

### ⚠️ 重要：确保生成完整角色

**问题**：AI 有时会只生成角色的上半身或下半身，导致动画帧不完整。

**解决方案**：需要从两个层面确保完整角色：

#### 1. `--description` 中必须包含以下关键词**：

```bash
# ❌ 错误：没有强调完整角色
--description "A brave warrior holding sword"

# ✅ 正确：强调完整角色
--description "A full body warrior character, complete human figure from head to toe, 
holding sword, standing pose, no cut-off"
```

**必须包含的关键词**：

| 关键词 | 作用 |
|--------|------|
| `full body` | 明确要求全身 |
| `complete figure` | 完整形象 |
| `from head to toe` | 从头到脚 |
| `standing pose` | 站立姿势 |
| `no cut-off` | 不截断 |

**完整角色提示词模板**：
```
A full body [character type], complete figure from head to toe,
[detailed appearance description],
[clothing/accessories],
standing pose, full view, no cut-off,
[style keywords]
```

#### 2. 生成脚本已自动强化约束

脚本 `generate_row.py` 会在提示词中自动添加以下约束：

```
LAYOUT: Generate ONE single image arranged as a 4-column by 2-row grid (8 cells).
...
CRITICAL: Each cell MUST show the COMPLETE character from head to toe,
no cropping, no truncation, no half-body. The entire body must fit within each cell.
```

如果仍有帧不完整，可以删除问题帧后单独重新生成：
```bash
# 删除问题帧
rm ./run/character/decoded/idle.png
rm ./run/character/frames/idle_*.png

# 重新生成该动作
python scripts/generate_row.py --run-dir ./run/character --row idle --mode grid --force
```

### 坦克/载具类角色指南 ⚠️ 重要

坦克、装甲车等**轮式/履带式载具**与角色动画有很大不同，需要特别注意：

#### 核心问题：AI 会按文字描述生成图像

| 你写的描述 | AI 理解为 | 结果 |
|-----------|----------|------|
| `tank walk` | 坦克 + 走路 | 生成有腿的坦克 ❌ |
| `tank rolling` | 履带滚动 | 生成正常坦克 ✅ |
| `soldier march` | 行军 | 可能触发敏感词 ❌ |
| `soldier moving right` | 向右移动 | 正常 ✅ |

**结论**：描述**运动方式**，不要写**动作名称**。

#### 按角色类型的运动描述

**1. 人形角色**（战士、刺客、英雄等）
```
✅ walking, running, jumping, sneaking, dashing, sidestepping, staggering, tiptoeing
❌ marching, charging, assaulting
```

**2. 坦克/履带载具**
```
✅ rolling, driving, cruising, advancing, maneuvering, tracking
❌ walking, marching, stomping
```

**3. 轮式车辆**（汽车、摩托车等）
```
✅ driving, cruising, racing, drifting, swerving, skidding
❌ marching, walking, stomping
```

**4. 机器人（履带式）**
```
✅ rolling, tracking, advancing, maneuvering, wheeling
❌ marching, walking
```

**5. 机器人（悬浮式）**
```
✅ hovering, gliding, floating, sliding, jetting
❌ marching, walking
```

**6. 飞行器**（飞机、直升机等）
```
✅ flying, soaring, gliding, hovering, diving
❌ marching
```

**7. 船/潜艇**
```
✅ sailing, cruising, diving, surfacing, gliding
❌ marching
```

#### 敏感词问题

⚠️ **注意**：某些单词组合可能是敏感词（涉及政治、国际关系等），目前已知：

| 敏感词 | 原因 | 替代词 |
|--------|------|--------|
| `march` | 行军、可能涉及政治 | `rolling`, `advancing`, `moving` |
| `walk right` | 可能是某组织名称 | `moving right`, `advancing right` |
| `charge` | 冲锋、攻击 | `advancing`, `rushing` |
| `assault` | 攻击 | `attacking`, `firing` |

> 💡 敏感词范围很广，建议使用中性的运动描述词。

#### 颜色主题建议

⚠️ **精灵角色禁止使用绿色主题**（背景图不受影响）！

因为 chroma_key 使用 `#00FF00`（纯绿色）作为透明背景，角色中的绿色会被删除。

| ✅ 推荐颜色 | ❌ 避免颜色 | 原因 |
|------------|------------|------|
| 蓝色 `#4169E1` | 绿色 `#00FF00` | 被背景删除 |
| 紫色 `#8A2BE2` | 亮绿色 | 被背景删除 |
| 橙色 `#FF8C00` | 翠绿色 | 被背景删除 |
| 红色 `#DC143C` | 黄绿色 | 被背景删除 |
| 银色 `#C0C0C0` | 浅绿色 | 被背景删除 |

#### 坦克描述示例

```bash
# ✅ 正确的坦克描述
python scripts/prepare_run.py \
  --animation-mode game \
  --game-type platformer \
  --character-name "Blue Tank" \
  --description "A blue military tank with silver tracks, top-down view, classic 8-bit style, blue armored body, cannon turret, rolling forward" \
  --style platformer-16bit \
  --category "Battle Games" \
  --output-dir ./run/blue-tank

# ❌ 错误的坦克描述
  --description "A green military tank..."      # 绿色会被删除！
  --description "A tank walking forward..."    # tank 用脚走路！
  --description "Tank marching forward..."     # march 敏感词！
```

#### 动作描述映射

| 动作名 | 人形角色 | 坦克/载具 | 悬浮机器人 |
|--------|---------|----------|-----------|
| idle | standing still | stationary | hovering |
| move-right | walking right | rolling right | gliding right |
| move-left | walking left | rolling left | gliding left |
| attack | attacking | firing cannon | firing laser |

### 第 2 步：生成 base

```bash
python scripts/generate_base.py --run-dir ./run/super-red
```

产出 `decoded/base.png` 并复制为 `references/canonical-base.png`。**必须人工检查这张图**——后续每行动作都把它作为 identity 锚点。如果形象不对，先重跑这一步再做后面任何动作行。

### 第 3 步：生成动作行

```bash
python scripts/generate_row.py --run-dir ./run/super-red --row idle --mode grid --force
python scripts/generate_row.py --run-dir ./run/super-red --row walk-right --mode grid --force
# ... 其余动作
```

或一次跑完所有动作：
```bash
python scripts/generate_row.py --run-dir ./run/super-red --row all --mode grid --force
```

> ⚠️ **重要**：默认的 `auto` 模式在当前 Doubao API 版本**不生效**。**必须使用 `--mode grid` 参数**。

游戏角色中的 `walk-left` 需要单独生成（不能简单镜像 walk-right，因为游戏角色可能有武器等方向性元素）。如需镜像：
```bash
python scripts/derive_running_left.py --run-dir ./run/super-red --confirm-appropriate-mirror
```

### 第 4 步：收尾

```bash
python scripts/extract_frames.py     --run-dir ./run/super-red
python scripts/chroma_key.py        --run-dir ./run/super-red
# python scripts/remove_black_border.py --run-dir ./run/super-red  # ⚠️ 不推荐：过于激进，可能破坏角色边缘
python scripts/compose_atlas.py     --run-dir ./run/super-red
python scripts/package_pet.py       --run-dir ./run/super-red --slug super-red-v1 --output-dir ./assets/characters/player
python scripts/render_qa.py        --run-dir ./run/super-red
```

> ⚠️ **重要**：
> 1. 必须按顺序执行每个脚本
> 2. `remove_black_border.py` 不推荐使用，因为它会移除角色边缘像素
> 3. 如需改善图片质量，请使用可选的 AI 背景移除（见下文）

#### chroma_key.py 处理说明

`chroma_key.py` 会自动检测并移除以下类型的背景色：
- ✅ 绿色背景 (`#00FF00`)
- ✅ 白色背景 (高亮度)
- ✅ 蓝色背景 (高饱和度)
- ✅ 灰色背景 (中等亮度)

#### remove_black_border.py 处理说明

`remove_black_border.py` 会移除帧边缘的黑色边框伪影：
- 检测边缘 3 像素宽度区域
- 移除纯黑色 (`RGB < 30`) 的边缘像素
- 将其设为透明

#### remove_all_lines.py 处理说明（增强版线条移除）

如果某些帧仍有黑色线条问题，可以使用增强版的线条移除脚本：
```bash
# Windows PowerShell
.\scripts\run_remove_lines.bat

# 或者分步执行
powershell -ExecutionPolicy Bypass -File "scripts\analyze_lines.ps1"   # 分析线条
powershell -ExecutionPolicy Bypass -File "scripts\remove_lines.ps1"   # 移除线条

# Python 版本
python scripts/remove_all_lines.py --run-dir ./run/super-red --action analyze
python scripts/remove_all_lines.py --run-dir ./run/super-red --action remove
```

**这个脚本会：**
- 扫描整个帧图像（不只是边缘）
- 检测连续暗色像素（竖向或横向）
- 移除超过最小长度的线条（默认30像素）
- 重建 spritesheet.png

**调整参数：**
- `--threshold`: 暗色像素阈值（默认50，值越小越严格）
- `--min-streak`: 最小线条长度（默认30像素）

```bash
# 更严格的检测
python scripts/remove_all_lines.py --run-dir ./run/super-red --action remove --threshold 40 --min-streak 20
```

> ⚠️ **警告**：`remove_all_lines.py` 和 `remove_lines.ps1` 可能影响角色质量，建议仅在有明显线条瑕疵时谨慎使用。

#### 可选的 AI 背景移除（推荐用于改善图片质量）

如果抠图后仍有背景残留，可以使用 AI 背景移除脚本：

```bash
# 处理游戏项目的所有角色（玩家 + 敌方）
python scripts/ai_bg_remove_game.py

# 处理特定角色的帧图片
python scripts/ai_bg_remove_frames.py
```

**注意**：
- 这是**可选步骤**，不影响游戏可玩性
- AI 背景移除使用 rembg 库，执行时间较长
- 如果执行遇到问题或时间过长，可以跳过

#### 打包到 assets 目录

使用 `package_pet.py` 的 `--output-dir` 参数直接打包到游戏 assets 目录：

```bash
# 打包玩家角色
python scripts/package_pet.py \
  --run-dir ./run/pig-soldier \
  --slug pig-soldier \
  --output-dir ./assets/characters/player

# 打包敌方角色（需要单独生成！）
python scripts/package_pet.py \
  --run-dir ./run/monkey-soldier \
  --slug monkey-soldier \
  --output-dir ./assets/characters/enemy
```

> ⚠️ **重要**：敌我角色必须使用**不同的 run 目录**分别生成！

#### 一键生成所有角色

使用 `generate_all.py` 可以一键生成玩家和敌方角色：

```bash
cd scripts

python generate_all.py \
  --player "Pig Soldier" \
  --player-desc "A brave pig soldier in green military uniform" \
  --enemy "Monkey Soldier" \
  --enemy-desc "A fierce monkey soldier in red uniform" \
  --output-dir ./run \
  --style platformer-16bit \
  --category "Action Adventure"
```

最终产物落在 `run/<character>/final/`：

```
run/super-red/
├── decoded/<row>.png            (Seedream 原始输出)
├── frames/<row>_<0..7>.png      (192x208 透明帧)
├── final/spritesheet.png
├── final/spritesheet.webp
├── final/character.json
└── qa/contact-sheet.png, qa/idle.gif, qa/walk-right.gif
```

## 宠物模式保留兼容

原有的宠物动画功能完全保留，使用 `--animation-mode pet`：

```bash
python scripts/prepare_run.py \
  --animation-mode pet \
  --character-name "My Pet" \
  --description "A cute cyberpunk hamster" \
  --style codex-pixel \
  --output-dir ./run/my-pet
```

## 风格与效果规则（必须遵守）

### 16-bit 平台游戏风格（默认游戏风格）

- 复古像素游戏美学，SNES/Genesis 时代风格
- 干净清晰的像素艺术风格，中等头身比（3-4 头身）
- 粗细适中的描边（2-3px）
- 大而可读的眼睛
- 简洁平面着色，不超过 4-6 色
- 角色轮廓在 192x208 下清晰可辨

### 禁止出现的元素

**所有帧通用禁止：**
- 精修插画、画家手感、3D 渲染、写实纹理
- 柔和渐变、抗锯齿柔化
- 投影、接触阴影、地面阴影、辉光
- 速度线、动作条、残影、模糊
- 离体的星星、漂浮粒子、散落的尘
- 文字、标签、帧编号、UI 面板
- 白色或黑色背景、风景
- Chroma-key 绿色渗入角色本体

**游戏角色额外禁止：**
- 生命条或伤害数字
- 受击闪烁效果
- 无敌星星或闪光
- 能量提升光环
- 硬币生成粒子
- 移动尾迹（普通移动时）

## 游戏角色与宠物动画的关键区别

| 维度 | 宠物动画 | 游戏角色动画 |
|------|----------|--------------|
| 动作风格 | 随意、情感化 | 精确、功能化 |
| 动作描述 | "happy"、"failed" | "attack"、"shoot" |
| 方向性 | running-left 可镜像 | walk-left 需独立生成 |
| 角色比例 | 2-3 头身为主 | 3-6 头身更常见 |
| 动作优先级 | 情感表达优先 | 游戏功能优先 |
| 循环要求 | idle 最重要 | 所有动作需可循环 |

## Identity Lock（身份锁定）

每次生成动作行都把 `references/canonical-base.png` 作为第一张参考图重新挂上。Row prompt 中包含："保持与参考图 1 完全一致的角色：同一头型、面部、花纹、配色、道具、描边粗细和轮廓"。

## 修复流程

满足以下任一条件，该行视为失败：
- Identity 漂移（看起来像相关但不同的角色）
- 帧数不对（grid 路径出现空 cell）
- Chroma key 渗入了角色本体颜色
- 出现禁用的离体特效、阴影、动作线

只修这一行：
```bash
python scripts/generate_row.py --run-dir ./run/super-red --row <row> --force
```

## 布局引导生成

如果需要重新生成布局引导图：
```bash
# 生成所有布局引导
python scripts/build_layout_guides.py --mode all

# 只生成游戏角色布局引导
python scripts/build_layout_guides.py --mode game

# 只生成宠物布局引导
python scripts/build_layout_guides.py --mode pet
```

## 部署到 TRAE

`game_design/` 是一个标准的 TRAE Skill 文件夹（包含 `SKILL.md`），三种安装方式任选其一：

| 方式 | 命令 / 操作 |
|------|------------|
| **项目级** | 把 `game_design/` 拷进项目根的 `.trae/skills/` 目录 |
| **全局级** | 国内版 `~/.trae-cn/skills/`；国际版 `~/.trae/skills/` |
| **设置面板上传** | 先 `python scripts/pack_skill.py` 打包出 zip，然后导入 |

安装完成后，在 TRAE 对话框用自然语言触发即可，例如：

> 帮我设计一个超级马里奥风格的游戏角色：红色帽子、蓝色衣服、大胡子

## 已知问题

### 问题1：auto 模式只返回1帧

**解决方案**：使用 `--mode grid` 参数强制使用 4×2 网格模式。

### 问题2：walk-left / running-left 方向

游戏角色动画中，walk-left 需要单独生成。如果角色完全对称，可以使用镜像脚本：
```bash
python scripts/derive_running_left.py --run-dir ./run/xxx --confirm-appropriate-mirror
```

## 进一步资料

- 游戏角色动作规范 → [references/game-animation-actions.md](references/game-animation-actions.md)
- 游戏角色基础规格 → [references/game-character-specs.md](references/game-character-specs.md)
- 详细 prompt 规范、Seedream 请求体字段 → [REFERENCE.md](REFERENCE.md)
- 四个端到端示例（宠物模式）→ [EXAMPLES.md](EXAMPLES.md)
