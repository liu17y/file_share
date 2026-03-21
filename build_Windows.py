#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AuroraShare 打包脚本
支持打包后使用 config/config.json 作为配置文件
"""

import os
import sys
import subprocess
import shutil
import glob
import json
from datetime import datetime


def print_color(text, color='green'):
    """彩色打印"""
    colors = {
        'green': '92m',
        'red': '91m',
        'yellow': '93m',
        'blue': '94m',
        'purple': '95m',
        'cyan': '96m',
    }
    if sys.platform == 'win32':
        print(text)
    else:
        color_code = colors.get(color, '92m')
        print(f"\033[{color_code}{text}\033[0m")


def clean_build():
    """清理构建文件"""
    dirs_to_clean = ['dist', 'build', '__pycache__', 'build_logs']
    files_to_clean = ['*.spec']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print_color(f"清理目录: {dir_name}/", 'yellow')
            try:
                shutil.rmtree(dir_name)
            except Exception as e:
                print_color(f"  清理失败: {e}", 'red')

    for pattern in files_to_clean:
        for file in glob.glob(pattern):
            print_color(f"清理文件: {file}", 'yellow')
            try:
                os.remove(file)
            except Exception as e:
                print_color(f"  清理失败: {e}", 'red')


def check_icon():
    """检查图标文件"""
    icon_files = ['icon.ico', 'logo.ico', 'app.ico']

    for icon in icon_files:
        if os.path.exists(icon):
            print_color(f"找到图标文件: {icon}", 'green')
            return ['--icon', icon]

    print_color("未找到图标文件，使用默认图标", 'yellow')
    return []


def check_requirements():
    """检查必要文件"""
    required_files = [
        'run.py',
        'backend/main.py',
        'backend/config.py',
        'backend/logger.py',
        'backend/file_manager.py',
        'backend/upload_manager.py',
        'frontend/index.html',
        'frontend/admin.html'
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print_color("缺少必要文件:", 'red')
        for file in missing_files:
            print_color(f"  - {file}", 'red')
        return False

    print_color("所有必要文件检查通过", 'green')
    return True


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_color(f"Python版本过低: {version.major}.{version.minor}.{version.micro}", 'red')
        print_color("需要 Python 3.7 或更高版本", 'red')
        return False

    print_color(f"Python版本: {version.major}.{version.minor}.{version.micro}", 'green')
    return True


def install_dependencies():
    """安装依赖"""
    print_color("\n安装依赖...", 'blue')

    # 安装 PyInstaller
    try:
        print_color("  安装 PyInstaller...", 'cyan')
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"],
            capture_output=True,
            text=True,
            check=True
        )
        print_color("  PyInstaller 安装成功", 'green')
    except subprocess.CalledProcessError as e:
        print_color(f"  PyInstaller 安装失败: {e}", 'red')
        if e.stderr:
            print_color(f"  错误: {e.stderr}", 'red')
        return False

    # 安装项目依赖
    try:
        if os.path.exists('backend/requirements.txt'):
            print_color("  安装项目依赖...", 'cyan')
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"],
                capture_output=True,
                text=True,
                check=True
            )
            print_color("  项目依赖安装成功", 'green')
        else:
            print_color("  未找到 requirements.txt，跳过依赖安装", 'yellow')
    except subprocess.CalledProcessError as e:
        print_color(f"  项目依赖安装失败: {e}", 'red')
        if e.stderr:
            print_color(f"  错误: {e.stderr}", 'red')
        return False

    return True


def prepare_build():
    """准备打包环境"""
    print_color("\n准备打包环境...", 'blue')

    # 确保 backend/__init__.py 存在
    init_file = 'backend/__init__.py'
    if not os.path.exists(init_file):
        print_color(f"  创建 {init_file}", 'cyan')
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('# AuroraShare backend package\n')

    # 创建配置文件模板
    create_config_template()

    return True


def create_config_template():
    """创建配置文件模板"""
    config_template = {
        "base_dir": "data/uploads",
        "port": 8000,
        "port_range_start": 8000,
        "port_range_end": 8010,
        "host": "0.0.0.0",
        "max_upload_size_mb": 1024,
        "auto_open_browser": True,
        "debug": False,
        "version": "1.0.0"
    }

    # 保存模板到 dist 目录（打包后会被复制）
    template_path = 'config.json.template'
    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(config_template, f, indent=2, ensure_ascii=False)

    print_color(f"  已创建配置文件模板: {template_path}", 'green')


def create_auxiliary_files(dist_dir):
    """创建辅助文件"""
    print_color("\n创建辅助文件...", 'blue')

    # 1. 创建 config 目录和默认配置文件
    config_dir = os.path.join(dist_dir, 'config')
    os.makedirs(config_dir, exist_ok=True)

    config_file = os.path.join(config_dir, 'config.json')
    if not os.path.exists(config_file):
        default_config = {
            "base_dir": "data/uploads",
            "port": 8000,
            "port_range_start": 8000,
            "port_range_end": 8010,
            "host": "0.0.0.0",
            "max_upload_size_mb": 1024,
            "auto_open_browser": True,
            "debug": False,
            "version": "1.0.0"
        }
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print_color(f"  已创建默认配置文件: config/config.json", 'green')

    # 2. 创建启动脚本
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
    startup_path = os.path.join(dist_dir, '启动AuroraShare.bat')
    with open(startup_path, 'w', encoding='utf-8') as f:
        f.write(startup_bat)
    print_color(f"  已创建启动脚本: 启动AuroraShare.bat", 'green')

    # 3. 创建 URL 快捷方式
    url_content = '''[InternetShortcut]
URL=http://localhost:8000
IDList=
HotKey=0
IconFile=AuroraShare.exe
IconIndex=0
'''
    url_path = os.path.join(dist_dir, 'AuroraShare.url')
    with open(url_path, 'w', encoding='utf-8') as f:
        f.write(url_content)
    print_color(f"  已创建快捷链接: AuroraShare.url", 'green')

    # 4. 创建说明文件
    readme_content = f'''AuroraShare 文件共享系统 v1.0
构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📁 文件说明:
  AuroraShare.exe        - 主程序
  启动AuroraShare.bat    - 启动脚本（双击运行）
  AuroraShare.url        - 快速访问链接
  config/                - 配置目录
    └── config.json      - 配置文件（可修改）
  data/                  - 数据目录（运行后自动创建）
    └── uploads/         - 上传文件存储位置
  logs/                  - 日志目录（运行后自动创建）

🚀 快速开始:
  1. 双击运行 "启动AuroraShare.bat" 或 "AuroraShare.exe"
  2. 等待程序启动（首次启动较慢）
  3. 自动打开浏览器访问 http://localhost:8000
  4. 开始上传和共享文件

⚙️ 配置说明:
  编辑 config/config.json 文件:
  - base_dir: 文件存储目录（支持绝对路径或相对路径）
  - port: 服务端口（默认8000）
  - host: 监听地址（默认0.0.0.0）
  - auto_open_browser: 是否自动打开浏览器
  - max_upload_size_mb: 最大上传大小（MB）

📝 配置示例:
  {{"base_dir": "D:\\\\file-share", "port": 8080}}

🐛 故障排除:
  1. 如果无法启动，查看 logs 目录下的日志文件
  2. 如果端口被占用，程序会自动寻找可用端口
  3. 如果浏览器未自动打开，手动访问 http://localhost:端口号

📞 技术支持:
  GitHub: https://github.com/yourname/AuroraShare

© 2025 Aurora Team
'''
    readme_path = os.path.join(dist_dir, 'README.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print_color(f"  已创建说明文件: README.txt", 'green')

    # 5. 创建数据目录
    data_dir = os.path.join(dist_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    uploads_dir = os.path.join(data_dir, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    print_color(f"  已创建数据目录: data/uploads/", 'green')

    # 6. 创建日志目录
    logs_dir = os.path.join(dist_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    print_color(f"  已创建日志目录: logs/", 'green')


def build():
    """执行打包"""
    print_color("=" * 60, 'purple')
    print_color("AuroraShare 打包工具 v1.0", 'purple')
    print_color("=" * 60, 'purple')
    print()

    # 检查环境
    print_color("[1/6] 检查环境...", 'blue')
    if not check_python_version():
        return False
    if not check_requirements():
        return False
    print()

    # 清理旧文件
    print_color("[2/6] 清理旧构建文件...", 'blue')
    clean_build()
    print()

    # 准备打包环境
    print_color("[3/6] 准备打包环境...", 'blue')
    if not prepare_build():
        return False
    print()

    # 安装依赖
    print_color("[4/6] 安装依赖...", 'blue')
    if not install_dependencies():
        return False
    print()

    # 准备打包命令
    print_color("[5/6] 开始打包...", 'blue')

    # 基础命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "AuroraShare",
        "--add-data", f"frontend{os.pathsep}frontend",
        "--add-data", f"backend{os.pathsep}backend",
        "--add-data", f"config.json.template{os.pathsep}.",
    ]

    # 添加图标
    icon_args = check_icon()
    cmd.extend(icon_args)

    # 添加隐藏导入
    hidden_imports = [
        "uvicorn",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "aiofiles",
        "watchfiles",
        "python_multipart",
        "backend.logger",
        "logging",
        "logging.handlers",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # 收集所有包
    collect_all = [
        "fastapi",
        "starlette",
        "pydantic",
    ]

    for package in collect_all:
        cmd.extend(["--collect-all", package])

    # 其他选项
    cmd.extend([
        "--clean",
        "--noconfirm",
        "run.py"
    ])

    # 显示打包信息
    print_color(f"打包配置:", 'cyan')
    print(f"  输出名称: AuroraShare.exe")
    print(f"  打包模式: 单文件模式")
    print(f"  包含资源: frontend/, backend/")
    print(f"  隐藏导入: {len(hidden_imports)} 个模块")
    print()

    # 执行打包
    print_color("正在打包，请耐心等待（可能需要几分钟）...", 'yellow')
    print()

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # 显示打包输出（最后20行）
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines[-20:]:
                if line.strip():
                    print(f"  {line}")

        print_color("\n[6/6] 打包完成！", 'green')

        # 检查生成的文件
        exe_path = os.path.join('dist', 'AuroraShare.exe')
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)
            print_color(f"\n✅ 打包成功！", 'green')
            print(f"📦 可执行文件: {os.path.abspath(exe_path)}")
            print(f"📊 文件大小: {size:.2f} MB")

            # 创建辅助文件
            create_auxiliary_files('dist')

            print_color("\n" + "=" * 60, 'purple')
            print_color("📁 打包输出目录结构:", 'cyan')
            print("dist/")
            print("├── AuroraShare.exe          # 主程序")
            print("├── 启动AuroraShare.bat      # 启动脚本")
            print("├── AuroraShare.url          # 快速访问链接")
            print("├── README.txt               # 使用说明")
            print("├── config/                  # 配置目录")
            print("│   └── config.json          # 配置文件（可修改）")
            print("├── data/                    # 数据目录")
            print("│   └── uploads/             # 上传文件存储")
            print("└── logs/                    # 日志目录（运行后创建）")
            print_color("=" * 60, 'purple')

            print_color("\n💡 使用说明:", 'cyan')
            print("   1. 双击运行 dist\\启动AuroraShare.bat 或 dist\\AuroraShare.exe")
            print("   2. 程序会自动打开浏览器")
            print("   3. 修改配置: 编辑 dist\\config\\config.json")
            print("   4. 上传文件保存在 dist\\data\\uploads 目录")
            print("   5. 日志文件保存在 dist\\logs 目录")

            print_color("\n⚙️ 配置说明:", 'cyan')
            print("   编辑 dist\\config\\config.json:")
            print('   - base_dir: 文件存储目录（如 "D:\\\\file-share"）')
            print("   - port: 服务端口（默认8000）")
            print("   - auto_open_browser: 是否自动打开浏览器")

            return True
        else:
            print_color("❌ 未找到生成的可执行文件", 'red')
            return False

    except subprocess.CalledProcessError as e:
        print_color(f"\n❌ 打包失败！", 'red')
        print_color(f"错误码: {e.returncode}", 'red')
        if e.stderr:
            print_color("错误信息:", 'red')
            print(e.stderr)
        return False
    except Exception as e:
        print_color(f"\n❌ 发生异常: {e}", 'red')
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    try:
        success = build()

        if success:
            print_color("\n✨ 打包完成！", 'green')
            print_color("程序文件位于 dist/ 目录", 'green')
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