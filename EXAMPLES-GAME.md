# 游戏角色动画示例

本文档展示如何使用改造后的技能来设计游戏角色的帧动画。

## 示例 1：超级马里奥风格角色

### 角色设计

设计一个类似马里奥的平台游戏角色：
- 红色帽子
- 蓝色工作服
- 大胡子
- 勇敢自信的表情
- 携带剑

### 步骤 1：准备运行目录

```bash
python scripts/prepare_run.py \
  --animation-mode game \
  --game-type platformer \
  --character-name "Super Red" \
  --description "A brave red plumber hero with a red cap, blue overalls, big bushy mustache, and confident determined smile. Wields a golden sword at his side. Pixel art style, 16-bit retro game aesthetic." \
  --style platformer-16bit \
  --category "Platform Games" \
  --output-dir ./run/super-red
```

### 步骤 2：生成基础形象

```bash
python scripts/generate_base.py --run-dir ./run/super-red
```

### 步骤 3：生成游戏动作

平台跳跃角色需要以下动作：
- idle - 待机站立
- walk-right - 向右行走
- walk-left - 向左行走
- jump - 跳跃
- crouch - 下蹲躲避
- attack - 攻击（挥剑）
- pickup - 拾取道具

生成所有动作：
```bash
python scripts/generate_row.py --run-dir ./run/super-red --row all --mode grid --force
```

### 步骤 4：收尾处理

```bash
python scripts/extract_frames.py --run-dir ./run/super-red
python scripts/chroma_key.py     --run-dir ./run/super-red
python scripts/compose_atlas.py  --run-dir ./run/super-red
python scripts/package_pet.py    --run-dir ./run/super-red --slug super-red--v1
python scripts/render_qa.py      --run-dir ./run/super-red
```

---

## 示例 2：动漫风格战士角色

### 角色设计

设计一个适合动作冒险游戏的战士角色：
- 银色盔甲
- 飘逸的披风
- 坚定的表情
- 双手巨剑

### 步骤 1：准备运行目录

使用完整动作集（11 个动作）：
```bash
python scripts/prepare_run.py \
  --animation-mode game \
  --game-type full \
  --character-name "Silver Guardian" \
  --description "A powerful warrior clad in gleaming silver armor with blue accents. Flows a deep red cape behind. Holds a massive broadsword with both hands. Determined and battle-ready expression. Anime-inspired game character art style." \
  --style platformer-anime \
  --category "Action Adventure" \
  --output-dir ./run/silver-guardian
```

### 步骤 2：生成基础形象

```bash
python scripts/generate_base.py --run-dir ./run/silver-guardian
```

### 步骤 3：生成游戏动作

完整动作集包括：
- idle - 待机站立
- walk-right - 向右行走
- walk-left - 向左行走
- jump - 跳跃
- fall - 下落
- crouch - 下蹲防御
- attack - 近战攻击
- shoot - 远程射击（可选）
- hit - 受击反应
- pickup - 拾取道具
- death - 死亡

生成所有动作：
```bash
python scripts/generate_row.py --run-dir ./run/silver-guardian --row all --mode grid --force
```

### 步骤 4：收尾处理

```bash
python scripts/extract_frames.py --run-dir ./run/silver-guardian
python scripts/chroma_key.py     --run-dir ./run/silver-guardian
python scripts/compose_atlas.py  --run-dir ./run/silver-guardian
python scripts/package_pet.py    --run-dir ./run/silver-guardian --slug silver-guardian--v1
python scripts/render_qa.py      --run-dir ./run/silver-guardian
```

---

## 示例 3：Q 版可爱风格角色

### 角色设计

设计一个类似星之卡比的可爱角色：
- 圆润的身体
- 粉色/蓝色渐变
- 大眼睛
- 头顶有小小的角或冠

### 步骤 1：准备运行目录

```bash
python scripts/prepare_run.py \
  --animation-mode game \
  --game-type platformer \
  --character-name "Star Puff" \
  --description "An adorable round pink puffball character with big sparkly eyes, tiny feet, and a small golden crown on top. Floats slightly off the ground. Cheerful and mischievous expression. Chibi cute platformer style." \
  --style platformer-chibi \
  --category "Platform Games" \
  --output-dir ./run/star-puff
```

### 步骤 2-4

按照标准流程生成动作和收尾。

---

## 动作优先级建议

### 核心优先级（必须）

| 动作 | 用途 | 重要性 |
|------|------|--------|
| idle | 等待玩家输入时播放 | ⭐⭐⭐⭐⭐ |
| walk-right | 向右移动 | ⭐⭐⭐⭐⭐ |
| walk-left | 向左移动 | ⭐⭐⭐⭐⭐ |
| jump | 跳跃动作 | ⭐⭐⭐⭐⭐ |

### 重要优先级（推荐）

| 动作 | 用途 | 重要性 |
|------|------|--------|
| attack | 战斗系统 | ⭐⭐⭐⭐ |
| crouch | 躲避/下蹲攻击 | ⭐⭐⭐⭐ |
| pickup | 道具交互 | ⭐⭐⭐ |

### 可选优先级（增强）

| 动作 | 用途 | 重要性 |
|------|------|--------|
| shoot | 远程攻击 | ⭐⭐⭐ |
| fall | 下落反馈 | ⭐⭐⭐ |
| hit | 受击反馈 | ⭐⭐⭐ |
| death | 死亡表现 | ⭐⭐ |

---

## 镜像使用指南

### 什么时候可以使用镜像

- ✅ idle 待机动画（完全对称）
- ✅ 简单的行走动画（无方向性武器/道具）
- ✅ 跳跃动画（无方向性道具）

### 什么时候必须单独生成

- ❌ 带武器的行走/攻击
- ❌ 有披风/长发飘动的动画
- ❌ 有单侧装备/装饰的角色
- ❌ 射击/投掷动画

### 镜像命令

如果角色完全对称，可以使用镜像生成 walk-left：

```bash
python scripts/derive_running_left.py \
  --run-dir ./run/super-red \
  --confirm-appropriate-mirror \
  --decision-note "Character has no side-specific markings, safe to mirror"
```

---

## 调试和修复

### 检查失败的行

```bash
# 查看 jobs.json 中的状态
cat ./run/super-red/jobs.json | grep -A5 "status"
```

### 重新生成单个动作

```bash
# 只重跑 attack 行
python scripts/generate_row.py --run-dir ./run/super-red --row attack --force
```

### 检查布局引导

确保布局引导图存在：
```bash
ls ./references/layout-guides/game/
```

如果缺失，重新生成：
```bash
python scripts/build_layout_guides.py --mode game
```

---

## 常见问题

### Q: 生成的动画帧数不对？

**A**: 确保使用 `--mode grid` 参数。auto 模式在当前 API 版本不生效。

### Q: 角色形象漂移？

**A**: 
1. 检查 `references/canonical-base.png` 是否正确
2. 重新运行 `generate_base.py` 生成正确的 base
3. 使用 `--force` 参数重跑相关动作行

### Q: Chroma key 绿色渗入角色？

**A**: 检查 `chroma_key.py` 的容差设置，增加 `--chroma-tolerance` 参数的值。

### Q: 行走动画看起来不自然？

**A**: 行走动画必须包含：
- 明显的脚部着地-离地交替
- 身体轻微上下起伏
- 手臂与腿部协调摆动
- 每个帧之间有清晰差异

---

## 输出文件

最终输出位于 `run/<character>/final/`：

```
run/super-red/final/
├── spritesheet.png          # PNG 格式精灵图
├── spritesheet.webp         # WebP 格式精灵图（推荐）
├── character.json            # 动画配置 JSON
├── qa/
│   ├── contact-sheet.png    # 联系表（所有动作预览）
│   ├── idle.gif             # 各动作 GIF 预览
│   ├── walk-right.gif
│   ├── walk-left.gif
│   └── ...
```

`character.json` 包含动画配置，可直接导入游戏引擎使用。
