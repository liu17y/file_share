#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AuroraShare 打包脚本（支持图标和日志）
"""

import os
import sys
import subprocess
import shutil
import glob
from datetime import datetime


def print_color(text, color='green'):
    """彩色打印"""
    colors = {
        'green': '92m',
        'red': '91m',
        'yellow': '93m',
        'blue': '94m',
        'purple': '95m',
    }
    if sys.platform == 'win32':
        print(text)
    else:
        color_code = colors.get(color, '92m')
        print(f"\033[{color_code}{text}\033[0m")


def clean_build():
    """清理构建文件"""
    dirs_to_clean = ['dist', 'build', '__pycache__']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print_color(f"清理目录: {dir_name}/", 'yellow')
            shutil.rmtree(dir_name)

    for pattern in files_to_clean:
        for file in glob.glob(pattern):
            print_color(f"清理文件: {file}", 'yellow')
            os.remove(file)


def check_icon():
    """检查图标文件"""
    icon_files = ['icon.ico', 'logo.ico', 'app.ico']

    for icon in icon_files:
        if os.path.exists(icon):
            print_color(f"找到图标文件: {icon}", 'green')
            return ['--icon', icon]

    print_color("未找到图标文件，使用默认图标", 'yellow')
    return []


def install_dependencies():
    """安装依赖"""
    print_color("\n安装 PyInstaller...", 'blue')
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"], check=False)

    if os.path.exists('backend/requirements.txt'):
        print_color("安装项目依赖...", 'blue')
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"], check=False)


def build():
    """执行打包"""
    print_color("=" * 60, 'purple')
    print_color("AuroraShare 打包工具 v1.0", 'purple')
    print_color("=" * 60, 'purple')
    print()

    # 清理旧文件
    print_color("[1/5] 清理旧文件...", 'blue')
    clean_build()

    # 安装依赖
    print_color("[2/5] 安装依赖...", 'blue')
    install_dependencies()

    # 准备打包命令
    print_color("[3/5] 准备打包...", 'blue')

    # 基础命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "AuroraShare",
        "--add-data", f"frontend{os.pathsep}frontend",
        "--add-data", f"backend{os.pathsep}backend",
        "--add-data", f"backend{os.pathsep}backend",
    ]

    # 添加图标
    icon_args = check_icon()
    cmd.extend(icon_args)

    # 添加隐藏导入
    hidden_imports = [
        "uvicorn", "uvicorn.loops", "uvicorn.loops.auto",
        "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan", "uvicorn.lifespan.on",
        "aiofiles", "watchfiles", "python_multipart",
        "backend.logger",  # 日志模块
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # 收集所有包
    collect_all = ["fastapi", "starlette", "pydantic"]
    for package in collect_all:
        cmd.extend(["--collect-all", package])

    # 其他选项
    cmd.extend([
        "--clean",
        "--noconfirm",
        "run.py"
    ])

    # 显示打包信息
    print_color(f"打包配置:", 'green')
    print(f"  输出名称: AuroraShare.exe")
    print(f"  打包模式: 单文件模式")
    print(f"  包含资源: frontend/, backend/")
    print(f"  隐藏导入: {len(hidden_imports)} 个模块")
    print()

    # 执行打包
    print_color("[4/5] 开始打包（可能需要几分钟）...", 'blue')
    print_color("请耐心等待...", 'yellow')
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        if result.stdout:
            # 只显示最后几行输出
            lines = result.stdout.split('\n')
            for line in lines[-20:]:
                if line.strip():
                    print(f"  {line}")

        print_color("\n[5/5] 打包完成！", 'green')

        # 检查生成的文件
        exe_path = os.path.join('dist', 'AuroraShare.exe')
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print_color(f"\n✅ 打包成功！", 'green')
            print(f"📦 可执行文件: {os.path.abspath(exe_path)}")
            print(f"📊 文件大小: {size:.2f} MB")

            # 创建辅助文件
            create_auxiliary_files()

            print_color("\n💡 使用说明:", 'cyan')
            print("   1. 双击运行 dist\\AuroraShare.exe")
            print("   2. 程序会自动打开浏览器")
            print("   3. 上传文件保存在 data\\uploads 目录")
            print("   4. 日志文件保存在 logs 目录")
            print("   5. 配置文件保存在 config 目录")

            return True
        else:
            print_color("❌ 未找到生成的可执行文件", 'red')
            return False

    except subprocess.CalledProcessError as e:
        print_color(f"\n❌ 打包失败！", 'red')
        if e.stderr:
            print("错误信息:")
            print(e.stderr)
        return False
    except Exception as e:
        print_color(f"\n❌ 发生异常: {e}", 'red')
        import traceback
        traceback.print_exc()
        return False


def create_auxiliary_files():
    """创建辅助文件"""
    dist_dir = 'dist'

    # 创建启动脚本
    startup_bat = '''@echo off
chcp 65001 >nul
title AuroraShare
echo ========================================
echo   AuroraShare 文件共享系统
echo ========================================
echo.
echo 正在启动服务器...
echo.
echo 访问地址: http://localhost:8000
echo.
echo 提示: 按 Ctrl+C 停止服务
echo ========================================
echo.
AuroraShare.exe
pause
'''

    with open(os.path.join(dist_dir, '启动AuroraShare.bat'), 'w', encoding='utf-8') as f:
        f.write(startup_bat)

    # 创建 URL 快捷方式
    url_content = '''[InternetShortcut]
URL=http://localhost:8000
IDList=
HotKey=0
IconFile=AuroraShare.exe
IconIndex=0
'''

    with open(os.path.join(dist_dir, 'AuroraShare.url'), 'w', encoding='utf-8') as f:
        f.write(url_content)

    # 创建说明文件
    readme_content = f'''AuroraShare 文件共享系统 v1.0
构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📁 文件说明:
  AuroraShare.exe        - 主程序
  启动AuroraShare.bat    - 启动脚本（双击运行）
  AuroraShare.url        - 快速访问链接
  README.txt             - 本说明文件

🚀 快速开始:
  1. 双击运行 "启动AuroraShare.bat" 或 "AuroraShare.exe"
  2. 等待程序启动（首次启动较慢）
  3. 自动打开浏览器访问 http://localhost:8000
  4. 开始上传和共享文件

📂 数据目录（运行后自动创建）:
  data\\uploads\\         - 上传的文件存储位置
  logs\\                 - 日志文件
  config\\               - 配置文件

⚙️ 配置说明:
  - 默认端口: 8000
  - 修改端口: 编辑 config\\config.json
  - 日志级别: 在 config.json 中设置

🐛 故障排除:
  1. 如果无法启动，查看 logs 目录下的日志文件
  2. 如果端口被占用，修改配置文件中的端口
  3. 如果浏览器未自动打开，手动访问 http://localhost:8000

📞 技术支持:
  GitHub: https://github.com/yourname/AuroraShare
  问题反馈: https://github.com/yourname/AuroraShare/issues

© 2025 Aurora Team
'''

    with open(os.path.join(dist_dir, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print_color("\n📝 辅助文件已创建:", 'green')
    print("   - 启动AuroraShare.bat")
    print("   - AuroraShare.url")
    print("   - README.txt")


def main():
    """主函数"""
    try:
        success = build()

        if success:
            print_color("\n" + "=" * 60, 'purple')
            print_color("✨ 打包完成！", 'green')
            print_color("=" * 60, 'purple')
        else:
            print_color("\n❌ 打包失败，请检查错误信息", 'red')

        input("\n按回车键退出...")

    except KeyboardInterrupt:
        print_color("\n\n用户取消打包", 'yellow')
    except Exception as e:
        print_color(f"\n❌ 错误: {e}", 'red')
        input("\n按回车键退出...")


if __name__ == "__main__":
    main()