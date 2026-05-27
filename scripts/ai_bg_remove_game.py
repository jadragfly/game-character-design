# -*- coding: utf-8 -*-
"""
AI Background Removal for pig-contra-game
处理 assets/characters/ 下的 spritesheet
"""
import os
import sys
import shutil

# 添加技能路径
SKILL_DIR = r"C:\Users\HP\.trae-cn\skills\背景移除技能"
sys.path.insert(0, SKILL_DIR)

os.environ['NETRC'] = ''

# 路径配置
GAME_DIR = r"D:\impotent\skills\make_game\pig-contra-game"
ENGINE_JS = os.path.join(GAME_DIR, r"js\engine.js")

from skill import RemoveBgSkill
from PIL import Image

def split_spritesheet(spritesheet_path, frame_dir, frame_w=192, frame_h=208, rows=7, cols=8):
    """拆分 spritesheet 为单帧"""
    print(f"拆分 spritesheet: {spritesheet_path}")

    if not os.path.exists(spritesheet_path):
        print(f"文件不存在: {spritesheet_path}")
        return []

    img = Image.open(spritesheet_path).convert("RGBA")
    os.makedirs(frame_dir, exist_ok=True)

    frames = []
    row_names = ['idle', 'walk-right', 'walk-left', 'jump', 'crouch', 'attack', 'pickup']

    for row in range(min(rows, img.height // frame_h)):
        for col in range(min(cols, img.width // frame_w)):
            x = col * frame_w
            y = row * frame_h
            frame = img.crop((x, y, x + frame_w, y + frame_h))

            if row < len(row_names):
                frame_name = f"{row_names[row]}_{col}.png"
            else:
                frame_name = f"frame_{row}_{col}.png"

            frame_path = os.path.join(frame_dir, frame_name)
            frame.save(frame_path, format="PNG")
            frames.append(frame_path)

    img.close()
    print(f"拆分完成: {len(frames)} 帧")
    return frames

def process_frames(frames_dir):
    """处理单帧"""
    print("初始化 AI 模型...")
    skill = RemoveBgSkill(model_name='u2netp')

    frame_files = [f for f in os.listdir(frames_dir) if f.endswith('.png')]
    total = 0
    success = 0

    print(f"开始处理 {len(frame_files)} 帧...")
    for frame_file in frame_files:
        input_file = os.path.join(frames_dir, frame_file)
        output_file = os.path.join(frames_dir, frame_file.replace('.png', '_no_bg.png'))

        try:
            result = skill.remove_background(input_file, output_file)

            if result and os.path.exists(output_file):
                shutil.copy2(output_file, input_file)
                os.remove(output_file)
                success += 1
                print(".", end="", flush=True)
            else:
                print("X", end="", flush=True)
        except Exception as e:
            print(f"\nERROR: {frame_file} - {e}")
            print("X", end="", flush=True)

        total += 1

    print(f"\n完成: {success}/{total} 帧")
    return success, total

def compose_spritesheet(frame_dir, output_path, frame_w=192, frame_h=208, rows=7, cols=8):
    """合成 spritesheet"""
    print(f"合成 spritesheet: {output_path}")

    total_w = cols * frame_w
    total_h = rows * frame_h
    spritesheet = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))

    row_names = ['idle', 'walk-right', 'walk-left', 'jump', 'crouch', 'attack', 'pickup']

    for row in range(rows):
        for col in range(cols):
            x = col * frame_w
            y = row * frame_h

            frame_name = f"{row_names[row]}_{col}.png"
            frame_path = os.path.join(frame_dir, frame_name)

            if os.path.exists(frame_path):
                try:
                    frame = Image.open(frame_path).convert("RGBA")
                    spritesheet.paste(frame, (x, y))
                    frame.close()
                except Exception as e:
                    print(f"Warning: {frame_name} - {e}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    spritesheet.save(output_path, format="PNG")

    # 尝试保存 webp
    webp_path = output_path.replace('.png', '.webp')
    try:
        spritesheet.save(webp_path, format="PNG")
        print(f"保存: {webp_path}")
    except:
        pass

    spritesheet.close()
    print(f"保存: {output_path}")
    return output_path

def update_version():
    """更新版本号"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    version = f"v={timestamp}"
    print(f"新版本: {version}")

    with open(ENGINE_JS, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    new_content = re.sub(r"ASSET_VERSION\s*=\s*['\"][^'\"]+['\"]", f'ASSET_VERSION = "{version}"', content)

    with open(ENGINE_JS, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("更新 engine.js")

    # 更新其他 JS 文件
    for js_file in [r"js\enemy.js", r"js\player.js"]:
        js_path = os.path.join(GAME_DIR, js_file)
        if os.path.exists(js_path):
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = re.sub(r"engine\.js\?v=\d+", f"engine.js?{version}", content)
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"更新 {os.path.basename(js_file)}")

    return version

def process_character(character_dir, char_name):
    """处理一个角色"""
    print(f"\n{'='*50}")
    print(f"处理角色: {char_name}")
    print(f"{'='*50}")

    spritesheet_path = os.path.join(character_dir, "spritesheet.webp")
    frame_dir = os.path.join(character_dir, "frames_temp")

    # 如果没有 webp，尝试 png
    if not os.path.exists(spritesheet_path):
        spritesheet_path = os.path.join(character_dir, "spritesheet.png")

    if not os.path.exists(spritesheet_path):
        print(f"找不到 spritesheet: {spritesheet_path}")
        return 0

    # 1. 拆分 spritesheet
    split_spritesheet(spritesheet_path, frame_dir)

    # 2. AI 处理
    success, total = process_frames(frame_dir)

    if success > 0:
        # 3. 重新合成
        compose_spritesheet(frame_dir, spritesheet_path)

    # 4. 清理临时文件夹
    if os.path.exists(frame_dir):
        shutil.rmtree(frame_dir)

    return success

def main():
    print("=" * 50)
    print("AI Background Removal for pig-contra-game")
    print("=" * 50)
    print()

    # 处理玩家角色
    player_dir = os.path.join(GAME_DIR, r"assets\characters\player")
    process_character(player_dir, "Player (Pig Soldier)")

    # 处理敌人角色
    enemy_dir = os.path.join(GAME_DIR, r"assets\characters\enemy")
    process_character(enemy_dir, "Enemy (Monkey Soldier)")

    # 更新版本号
    version = update_version()

    print()
    print("=" * 50)
    print("完成! 刷新浏览器 (Ctrl+F5) 查看效果")
    print(f"版本: {version}")
    print("=" * 50)

if __name__ == "__main__":
    main()
