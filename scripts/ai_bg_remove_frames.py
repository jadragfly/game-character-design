# -*- coding: utf-8 -*-
"""
AI Background Removal for pig-soldier
使用 rembg 移除背景，并更新spritesheet
"""
import os
import sys
import shutil

# 添加技能路径
SKILL_DIR = r"C:\Users\HP\.trae-cn\skills\背景移除技能"
sys.path.insert(0, SKILL_DIR)

os.environ['NETRC'] = ''

# 路径配置
FRAMES_DIR = r"D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier\frames"
FINAL_DIR = r"D:\impotent\skills\make_game\pig-contra-game\run\pig-soldier\final"
ENGINE_JS = r"D:\impotent\skills\make_game\pig-contra-game\js\engine.js"

from skill import RemoveBgSkill

def process_frames():
    """处理所有帧图片"""
    print("初始化 AI 模型...")
    skill = RemoveBgSkill(model_name='u2netp')

    rows = ['idle', 'walk-right', 'walk-left', 'jump', 'crouch', 'attack', 'pickup']
    total = 0
    success = 0

    print("开始处理帧...")
    for row in rows:
        for i in range(8):
            input_file = os.path.join(FRAMES_DIR, f"{row}_{i}.png")
            output_file = os.path.join(FRAMES_DIR, f"{row}_{i}_no_bg.png")

            try:
                # AI 处理后生成 _no_bg.png 文件
                result = skill.remove_background(input_file, output_file)

                if result and os.path.exists(output_file):
                    # 用处理后的文件覆盖原文件
                    shutil.copy2(output_file, input_file)
                    os.remove(output_file)
                    success += 1
                    print(".", end="", flush=True)
                else:
                    print("X", end="", flush=True)
            except Exception as e:
                print(f"\nERROR: {input_file} - {e}")
                print("X", end="", flush=True)

            total += 1

    print(f"\n完成: {success}/{total} 帧")
    return success, total

def rebuild_spritesheet():
    """重建 spritesheet"""
    print("重建 spritesheet...")

    try:
        from PIL import Image
    except ImportError:
        print("需要安装 Pillow: pip install pillow")
        return None

    rows = ['idle', 'walk-right', 'walk-left', 'jump', 'crouch', 'attack', 'pickup']
    frame_size_w = 192
    frame_size_h = 234
    cols = 8

    total_height = len(rows) * frame_size_h
    total_width = cols * frame_size_w

    spritesheet = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))

    for row_idx, row in enumerate(rows):
        y = row_idx * frame_size_h
        for col_idx in range(8):
            frame_path = os.path.join(FRAMES_DIR, f"{row}_{col_idx}.png")
            if os.path.exists(frame_path):
                x = col_idx * frame_size_w
                try:
                    frame = Image.open(frame_path).convert("RGBA")
                    spritesheet.paste(frame, (x, y))
                    frame.close()
                except Exception as e:
                    print(f"Warning: Could not load {frame_path} - {e}")

    spritesheet_path = os.path.join(FINAL_DIR, "spritesheet.png")
    spritesheet.save(spritesheet_path, format="PNG")
    print(f"保存: {spritesheet_path}")

    # 同时保存 webp 版本
    webp_path = os.path.join(FINAL_DIR, "spritesheet.webp")
    spritesheet.save(webp_path, format="PNG")  # PIL 保存为 webp 需要额外库，这里用 PNG
    print(f"保存: {webp_path}")

    return spritesheet_path

def update_version():
    """更新版本号"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    version = f"v={timestamp}"
    print(f"新版本: {version}")

    # 更新 engine.js
    with open(ENGINE_JS, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    new_content = re.sub(r"ASSET_VERSION\s*=\s*['\"][^'\"]+['\"]", f'ASSET_VERSION = "{version}"', content)

    with open(ENGINE_JS, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("更新 engine.js")

    # 同时更新 enemy.js 和 player.js 的 import 版本
    enemy_js = r"D:\impotent\skills\make_game\pig-contra-game\js\enemy.js"
    player_js = r"D:\impotent\skills\make_game\pig-contra-game\js\player.js"

    for js_file in [enemy_js, player_js]:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = re.sub(r"engine\.js\?v=\d+", f"engine.js?{version}", content)
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"更新 {os.path.basename(js_file)}")

    return version

def main():
    print("=" * 50)
    print("AI Background Removal for pig-soldier")
    print("=" * 50)
    print()

    success, total = process_frames()

    if success > 0:
        rebuild_spritesheet()
        version = update_version()

        print()
        print("=" * 50)
        print("完成! 刷新浏览器 (Ctrl+F5) 查看效果")
        print(f"版本: {version}")
        print("=" * 50)
    else:
        print("没有处理任何文件")

if __name__ == "__main__":
    main()
