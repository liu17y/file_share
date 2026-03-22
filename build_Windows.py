#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AuroraShare 打包工具 v1.0
Python版本，实现与批处理脚本相同的功能
"""

import os
import sys
import subprocess
import shutil
import platform
import json
from pathlib import Path
from datetime import datetime

# 设置控制台编码为UTF-8 (Windows)
if platform.system() == 'Windows':
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class Colors:
    """控制台颜色代码"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def disable():
        """禁用颜色（Windows cmd不支持时）"""
        if platform.system() == 'Windows':
            Colors.GREEN = ''
            Colors.RED = ''
            Colors.YELLOW = ''
            Colors.BLUE = ''
            Colors.RESET = ''
            Colors.BOLD = ''


# 检测是否支持颜色
if platform.system() == 'Windows':
    # Windows下尝试启用ANSI支持
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        Colors.disable()


def print_header(text):
    """打印标题样式"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 40}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^40}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 40}{Colors.RESET}\n")


def print_success(text):
    """打印成功信息"""
    print(f"{Colors.GREEN}[✓] {text}{Colors.RESET}")


def print_error(text):
    """打印错误信息"""
    print(f"{Colors.RED}[✗] 错误: {text}{Colors.RESET}")


def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.YELLOW}[!] {text}{Colors.RESET}")


def print_info(text):
    """打印信息"""
    print(f"[*] {text}")


def run_command(cmd, cwd=None, check=True):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if check and result.returncode != 0:
            if result.stderr:
                print_error(f"命令执行失败: {result.stderr}")
            return False
        return result
    except Exception as e:
        if check:
            print_error(f"命令执行异常: {e}")
        return None


def check_python():
    """检查Python环境"""
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("Python 环境检查通过")
            print(f"   {result.stdout.strip()}")
            return True
        else:
            print_error("未找到 Python，请先安装 Python")
            return False
    except FileNotFoundError:
        print_error("未找到 Python，请先安装 Python")
        return False


def check_required_files():
    """检查必要文件是否存在"""
    required_files = [
        "run.py",
        "backend/main.py",
        "backend/config.py",
        "frontend/index.html"
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print_error("缺少必要文件:")
        for f in missing_files:
            print(f"   - {f}")
        return False

    print_success("必要文件检查通过")
    return True


def install_pyinstaller():
    """安装PyInstaller"""
    print_header("[1/5] 安装 PyInstaller")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"],
            check=True
        )
        print_success("PyInstaller 安装完成")
        return True
    except subprocess.CalledProcessError:
        print_error("PyInstaller 安装失败")
        return False


def install_dependencies():
    """安装项目依赖"""
    print_header("[2/5] 安装项目依赖")

    req_file = Path("backend/requirements.txt")
    if req_file.exists():
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
                check=False  # 不强制成功，有些依赖可能已安装
            )
            print_success("依赖检查完成")
        except Exception:
            print_warning("部分依赖安装失败，继续打包...")
    else:
        print_warning("未找到 requirements.txt，跳过依赖安装")

    return True


def clean_old_files():
    """清理旧的打包文件"""
    print_header("[3/5] 清理旧打包文件")

    dirs_to_remove = ["dist", "build"]
    for dir_name in dirs_to_remove:
        path = Path(dir_name)
        if path.exists():
            print_info(f"删除 {dir_name} 目录...")
            shutil.rmtree(path, ignore_errors=True)

    for spec_file in Path(".").glob("*.spec"):
        print_info(f"删除 {spec_file.name}...")
        spec_file.unlink()

    print_success("清理完成")
    return True


def create_config_template():
    """创建配置文件模板"""
    template_path = Path("config.json.template")
    if not template_path.exists():
        print_info("创建配置文件模板...")
        config_data = {
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
        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)


def build_exe():
    """执行打包命令"""
    print_header("[4/5] 开始打包程序")
    print("正在打包，请稍候...\n")

    # 创建配置文件模板
    create_config_template()

    # 检查图标文件
    icon_flag = []
    if Path("icon.ico").exists():
        print_success("找到图标文件: icon.ico")
        icon_flag = ["--icon=icon.ico"]
    else:
        print_warning("未找到图标文件 icon.ico，将使用默认图标")

    # 构建PyInstaller命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "AuroraShare",
        *icon_flag,
        "--add-data", f"frontend{os.pathsep}frontend",
        "--add-data", f"backend{os.pathsep}backend",
        "--add-data", f"config.json.template{os.pathsep}.",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.loops",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols",
        "--hidden-import", "uvicorn.protocols.http",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "aiofiles",
        "--hidden-import", "watchfiles",
        "--hidden-import", "python_multipart",
        "--hidden-import", "backend.logger",
        "--collect-all", "fastapi",
        "--collect-all", "starlette",
        "--collect-all", "pydantic",
        "--clean",
        "--noconfirm",
        "run.py"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.returncode != 0:
            print_error(f"打包失败: {result.stderr}")
            return False

        print_success("打包完成")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"打包失败")
        if e.stderr:
            print(e.stderr)
        return False
    except Exception as e:
        print_error(f"打包异常: {e}")
        return False


def create_dist_files():
    """创建dist目录中的辅助文件"""
    print_header("[5/5] 整理文件")

    exe_path = Path("dist/AuroraShare.exe")
    if not exe_path.exists():
        print_error("未找到生成的可执行文件")
        return False

    print_success(f"主程序生成成功")

    # 获取文件大小
    size_bytes = exe_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    print(f"     文件大小: {size_mb:.2f} MB\n")

    # 创建config目录和配置文件
    print_info("创建配置文件...")
    config_dir = Path("dist/config")
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "config.json"
    if not config_file.exists():
        config_data = {
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
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print_success("已创建配置文件: config/config.json")

    # 创建启动脚本
    print_info("创建启动脚本...")
    start_script = Path("dist/启动AuroraShare.bat")
    with open(start_script, "w", encoding="gbk") as f:
        f.write('@echo off\n')
        f.write('chcp 65001 >nul\n')
        f.write('title AuroraShare\n')
        f.write('echo ========================================\n')
        f.write('echo   AuroraShare 文件共享系统\n')
        f.write('echo ========================================\n')
        f.write('echo.\n')
        f.write('echo 正在启动服务器...\n')
        f.write('echo.\n')
        f.write('echo 访问地址: http://localhost:8000\n')
        f.write('echo.\n')
        f.write('echo 提示: 按 Ctrl+C 停止服务\n')
        f.write('echo ========================================\n')
        f.write('echo.\n')
        f.write('AuroraShare.exe\n')
        f.write('pause\n')
    print_success("已创建启动脚本: 启动AuroraShare.bat")

    # 创建快捷链接
    print_info("创建快速访问链接...")
    url_file = Path("dist/AuroraShare.url")
    with open(url_file, "w", encoding="utf-8") as f:
        f.write('[InternetShortcut]\n')
        f.write('URL=http://localhost:8000\n')
        f.write('IDList=\n')
        f.write('HotKey=0\n')
        f.write('IconFile=AuroraShare.exe\n')
        f.write('IconIndex=0\n')
    print_success("已创建快捷链接: AuroraShare.url")

    # 创建数据目录
    print_info("创建数据目录...")
    data_dir = Path("dist/data/uploads")
    data_dir.mkdir(parents=True, exist_ok=True)
    print_success("已创建数据目录: data/uploads/")

    # 创建日志目录
    print_info("创建日志目录...")
    logs_dir = Path("dist/logs")
    logs_dir.mkdir(exist_ok=True)
    print_success("已创建日志目录: logs/")

    # 创建说明文件
    print_info("创建说明文件...")
    readme_file = Path("dist/README.txt")
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(f"AuroraShare 文件共享系统 v1.0\n")
        f.write(f"构建日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("=" * 40 + "\n")
        f.write("文件说明\n")
        f.write("=" * 40 + "\n")
        f.write("  AuroraShare.exe        - 主程序\n")
        f.write("  启动AuroraShare.bat    - 启动脚本（双击运行）\n")
        f.write("  AuroraShare.url        - 快速访问链接\n")
        f.write("  config\\                - 配置目录\n")
        f.write("    └── config.json      - 配置文件（可修改）\n")
        f.write("  data\\                  - 数据目录\n")
        f.write("    └── uploads\\         - 上传文件存储位置\n")
        f.write("  logs\\                  - 日志目录（运行后自动创建）\n\n")
        f.write("=" * 40 + "\n")
        f.write("快速开始\n")
        f.write("=" * 40 + "\n")
        f.write("  1. 双击运行 \"启动AuroraShare.bat\" 或 \"AuroraShare.exe\"\n")
        f.write("  2. 等待程序启动（首次启动较慢）\n")
        f.write("  3. 自动打开浏览器访问 http://localhost:8000\n")
        f.write("  4. 开始上传和共享文件\n\n")
        f.write("=" * 40 + "\n")
        f.write("配置说明\n")
        f.write("=" * 40 + "\n")
        f.write("  编辑 config\\config.json 文件:\n")
        f.write("  - base_dir: 文件存储目录（支持绝对路径或相对路径）\n")
        f.write("  - port: 服务端口（默认8000）\n")
        f.write("  - host: 监听地址（默认0.0.0.0）\n")
        f.write("  - auto_open_browser: 是否自动打开浏览器\n")
        f.write("  - max_upload_size_mb: 最大上传大小（MB）\n\n")
        f.write('  配置示例:\n')
        f.write('  {"base_dir": "D:\\\\file-share", "port": 8080}\n\n')
        f.write("=" * 40 + "\n")
        f.write("故障排除\n")
        f.write("=" * 40 + "\n")
        f.write("  1. 如果无法启动，查看 logs 目录下的日志文件\n")
        f.write("  2. 如果端口被占用，程序会自动寻找可用端口\n")
        f.write("  3. 如果浏览器未自动打开，手动访问 http://localhost:端口号\n\n")
        f.write("=" * 40 + "\n")
        f.write("技术支持\n")
        f.write("=" * 40 + "\n")
        f.write("  GitHub: https://github.com/yourname/AuroraShare\n\n")
        f.write("© 2025 Aurora Team\n")

    print_success("已创建说明文件: README.txt")
    print_success("辅助文件创建完成")

    return True


def print_final_message():
    """打印最终成功信息"""
    print("\n" + "=" * 40)
    print(f"{Colors.GREEN}{Colors.BOLD}  打包成功！ ✨{Colors.RESET}")
    print("=" * 40)
    print(f"\n📦 输出目录: {Path('dist').absolute()}\n")
    print("📂 目录结构:")
    print("  dist\\")
    print("  ├── AuroraShare.exe          # 主程序")
    print("  ├── 启动AuroraShare.bat      # 启动脚本")
    print("  ├── AuroraShare.url          # 快速访问链接")
    print("  ├── README.txt               # 使用说明")
    print("  ├── config\\                  # 配置目录")
    print("  │   └── config.json          # 配置文件（可修改）")
    print("  ├── data\\                    # 数据目录")
    print("  │   └── uploads\\             # 上传文件存储")
    print("  └── logs\\                    # 日志目录（运行后创建）\n")
    print("💡 使用提示:")
    print("   1. 双击运行 dist\\启动AuroraShare.bat")
    print("   2. 程序会自动打开浏览器访问 http://localhost:8000")
    print("   3. 修改配置: 编辑 dist\\config\\config.json")
    print("   4. 上传文件保存在 dist\\data\\uploads 目录")
    print("   5. 日志文件保存在 dist\\logs 目录\n")
    print("⚙️ 配置示例（编辑 config\\config.json）:")
    print('   {')
    print('     "base_dir": "D:\\\\file-share",')
    print('     "port": 8080,')
    print('     "auto_open_browser": true')
    print('   }\n')
    print("=" * 40)


def main():
    """主函数"""
    # 设置控制台标题
    if platform.system() == 'Windows':
        os.system("title AuroraShare 打包工具")
        os.system("color 0A")

    print_header("AuroraShare 打包工具 v1.0")

    # 1. 检查Python环境
    if not check_python():
        input("\n按回车键退出...")
        sys.exit(1)
    print()

    # 2. 检查必要文件
    if not check_required_files():
        input("\n按回车键退出...")
        sys.exit(1)
    print()

    # 3. 安装PyInstaller
    if not install_pyinstaller():
        input("\n按回车键退出...")
        sys.exit(1)
    print()

    # 4. 安装依赖
    install_dependencies()
    print()

    # 5. 清理旧文件
    clean_old_files()
    print()

    # 6. 打包程序
    if not build_exe():
        print("\n请检查错误信息，常见问题：")
        print("1. Python 版本过低（需要 3.7+）")
        print("2. 缺少必要的依赖包")
        print("3. 路径中包含中文字符")
        input("\n按回车键退出...")
        sys.exit(1)
    print()

    # 7. 创建辅助文件
    if not create_dist_files():
        input("\n按回车键退出...")
        sys.exit(1)

    # 8. 打印最终信息
    print_final_message()

    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(0)
    except Exception as e:
        print_error(f"未知错误: {e}")
        input("\n按回车键退出...")
        sys.exit(1)