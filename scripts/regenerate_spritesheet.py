# -*- coding: utf-8 -*-
"""
重新生成 spritesheet - 从 decoded 目录开始
跳过去黑框步骤
"""
import os
import sys
import shutil
from datetime import datetime

# 添加游戏角色设计技能路径
SKILL_SCRIPTS = r"D:\impotent\skills\make_game\game-character-design\scripts"
sys.path.insert(0, SKILL_SCRIPTS)
os.chdir(SKILL_SCRIPTS)

GAME_DIR = r"D:\impotent\skills\make_game\pig-contra-game"
PIG_DIR = os.path.join(GAME_DIR, r"run\pig-soldier")

def regenerate_spritesheet():
    """从 decoded 重新生成 spritesheet"""

    print("=" * 50)
    print("重新生成 Pig-Soldier Spritesheet")
    print("=" * 50)
    print()

    # 1. 提取帧
    print("Step 1: 提取帧...")
    import extract_frames
    sys.argv = ["extract_frames.py", "--run-dir", PIG_DIR]
    result = extract_frames.main()
    if result != 0:
        print("  帧提取失败!")
        return False
    print("  完成!")

    # 2. 抠图处理（chroma key）
    print("Step 2: 抠图处理...")
    import chroma_key
    sys.argv = ["chroma_key.py", "--run-dir", PIG_DIR]
    result = chroma_key.main()
    if result != 0:
        print("  抠图失败!")
        return False
    print("  完成!")

    # 3. 合成精灵图
    print("Step 3: 合成精灵图...")
    import compose_atlas
    sys.argv = ["compose_atlas.py", "--run-dir", PIG_DIR]
    result = compose_atlas.main()
    if result != 0:
        print("  合成失败!")
        return False
    print("  完成!")

    return True

def copy_to_assets():
    """复制到 assets 目录"""

    print()
    print("Step 4: 复制到 assets 目录...")

    src = os.path.join(PIG_DIR, r"final\spritesheet.webp")
    dst_player = os.path.join(GAME_DIR, r"assets\characters\player\spritesheet.webp")
    dst_enemy = os.path.join(GAME_DIR, r"assets\characters\enemy\spritesheet.webp")

    if not os.path.exists(src):
        print(f"  源文件不存在: {src}")
        return False

    print(f"  复制到玩家目录...")
    shutil.copy2(src, dst_player)

    print(f"  复制到敌人目录...")
    shutil.copy2(src, dst_enemy)

    print("  完成!")
    return True

def update_version():
    """更新版本号"""
    print()
    print("Step 5: 更新版本号...")

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    version = f"v={timestamp}"
    print(f"  新版本: {version}")

    engine_js = os.path.join(GAME_DIR, r"js\engine.js")
    with open(engine_js, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    new_content = re.sub(r"ASSET_VERSION\s*=\s*['\"][^'\"]+['\"]", f'ASSET_VERSION = "{version}"', content)

    with open(engine_js, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("  更新 engine.js 完成!")

    # 更新其他 JS 文件引用
    for js_file in [r"js\enemy.js", r"js\player.js"]:
        js_path = os.path.join(GAME_DIR, js_file)
        if os.path.exists(js_path):
            with open(js_path, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = re.sub(r"engine\.js\?v=\d+", f"engine.js?{version}", content)
            new_content = re.sub(r"sprite-system\.js\?v=\d+", f"sprite-system.js?{version}", new_content)
            new_content = re.sub(r"audio\.js\?v=\d+", f"audio.js?{version}", new_content)
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  更新 {os.path.basename(js_file)} 完成!")

    return version

def main():
    if regenerate_spritesheet():
        if copy_to_assets():
            version = update_version()

            print()
            print("=" * 50)
            print(f"完成! 刷新浏览器 (Ctrl+F5) 查看效果")
            print(f"版本: {version}")
            print("=" * 50)
        else:
            print("复制到 assets 目录失败!")
    else:
        print("重新生成 spritesheet 失败!")

if __name__ == "__main__":
    main()
