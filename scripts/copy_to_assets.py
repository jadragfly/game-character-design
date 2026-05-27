# -*- coding: utf-8 -*-
"""
复制 spritesheet 到 assets 目录 - 纯复制，不处理
"""
import os
import shutil
from datetime import datetime

GAME_DIR = r"D:\impotent\skills\make_game\pig-contra-game"

def copy_spritesheet():
    """复制 spritesheet 到 assets 目录"""

    print("=" * 50)
    print("复制 Spritesheet 到 assets 目录")
    print("=" * 50)
    print()

    # 源文件：游戏角色设计生成的
    src = os.path.join(GAME_DIR, r"run\pig-soldier\final\spritesheet.webp")

    # 目标文件：游戏加载的
    dst_player = os.path.join(GAME_DIR, r"assets\characters\player\spritesheet.webp")
    dst_enemy = os.path.join(GAME_DIR, r"assets\characters\enemy\spritesheet.webp")

    # 检查源文件
    if not os.path.exists(src):
        print(f"源文件不存在: {src}")
        return

    print(f"源文件: {src}")
    print()

    # 复制玩家 spritesheet
    print(f"复制到玩家目录...")
    print(f"  目标: {dst_player}")
    shutil.copy2(src, dst_player)
    print("  完成!")

    # 复制敌人 spritesheet
    print(f"复制到敌人目录...")
    print(f"  目标: {dst_enemy}")
    shutil.copy2(src, dst_enemy)
    print("  完成!")

    # 更新版本号
    print()
    print("更新版本号...")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    version = f"v={timestamp}"
    print(f"新版本: {version}")

    engine_js = os.path.join(GAME_DIR, r"js\engine.js")
    with open(engine_js, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    new_content = re.sub(r"ASSET_VERSION\s*=\s*['\"][^'\"]+['\"]", f'ASSET_VERSION = "{version}"', content)

    with open(engine_js, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("更新 engine.js 完成!")

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
            print(f"更新 {os.path.basename(js_file)} 完成!")

    print()
    print("=" * 50)
    print(f"完成! 刷新浏览器 (Ctrl+F5) 查看效果")
    print(f"版本: {version}")
    print("=" * 50)

if __name__ == "__main__":
    copy_spritesheet()
