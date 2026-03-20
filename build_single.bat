@echo off
chcp 65001 >nul
cls

echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║   AuroraShare · 极光共享 - 单文件 EXE 打包工具          ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 📦 正在准备打包环境...
echo.

REM ==================== 检查 Python 环境 ====================
echo [1/6] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到 Python 环境
    pause
    exit /b 1
)
echo ✅ Python 环境检测通过
python --version
echo.

REM ==================== 安装依赖 ====================
echo [2/6] 安装项目依赖...
pip install -r backend\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
echo ✅ 依赖安装完成
echo.

REM ==================== 安装 PyInstaller ====================
echo [3/6] 安装 PyInstaller...
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
echo ✅ PyInstaller 安装完成
echo.

REM ==================== 创建启动脚本 ====================
echo [4/6] 创建启动脚本...

(
echo import sys
echo import os
echo import webbrowser
echo import time
echo from pathlib import Path
echo.
echo # 获取运行目录
echo if getattr^(sys, 'frozen', False^):
echo     BASE_DIR = Path^(sys.executable^).parent
echo else:
echo     BASE_DIR = Path^(__file__^).parent
echo.
echo # 设置工作目录
echo os.chdir^(BASE_DIR^)
echo.
echo # 添加路径
echo backend_path = BASE_DIR / "backend"
echo if str^(backend_path^) not in sys.path:
echo     sys.path.insert^(0, str^(backend_path^)^)
echo.
echo print^("=" * 60^)
echo print^("AuroraShare · 极光共享"^)
echo print^("=" * 60^)
echo print^(^)
echo print^("🚀 服务启动中..."^)
echo.
echo # 延迟打开浏览器
echo def open_browser^(^):
echo     time.sleep^(2^)
echo     try:
echo         webbrowser.open^("http://localhost:8000"^, new=2^)
echo         print^("✅ 已自动打开浏览器"^)
echo     except:
echo         print^("⚠️  请手动访问 http://localhost:8000"^)
echo.
echo # 启动浏览器线程
echo import threading
echo browser_thread = threading.Thread^target=open_browser^)
echo browser_thread.daemon = True
echo browser_thread.start^(^)
echo.
echo # 导入并运行
echo from main import start_server
echo print^("💡 按 Ctrl+C 停止服务"^)
echo print^(^)
echo start_server^(^)
) > run_standalone.py

echo ✅ 启动脚本创建完成
echo.

REM ==================== 开始打包 ====================
echo [5/6] 开始打包为单个 EXE 文件...
echo.
echo 🔨 这可能需要 3-5 分钟，请耐心等待...
echo.

REM 清理旧文件
if exist "build" rmdir /s /q build
if exist "*.spec" del /q *.spec
if exist "dist\AuroraShare.exe" del /q dist\AuroraShare.exe

pyinstaller ^
    --name "AuroraShare" ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --add-data "backend;backend" ^
    --add-data "frontend;frontend" ^
    --hidden-import fastapi ^
    --hidden-import uvicorn ^
    --hidden-import aiofiles ^
    --hidden-import asyncio ^
    --hidden-import threading ^
    --hidden-import webbrowser ^
    --hidden-import time ^
    run_standalone.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！
    pause
    exit /b 1
)

echo.
echo ✅ 打包成功！
echo.

REM ==================== 整理输出 ====================
echo [6/6] 整理输出文件...

REM 创建发布文件夹
if not exist "release" mkdir release

REM 复制 EXE
copy dist\AuroraShare.exe release\ >nul
copy run_standalone.py release\ >nul
copy backend\config.json release\ 2>nul
copy README.md release\ 2>nul

REM 创建使用说明
(
echo AuroraShare · 极光共享 - 使用说明
echo ════════════════════════════════════════
echo.
echo 📦 包含文件:
echo   - AuroraShare.exe      主程序（双击运行）
echo   - run_standalone.py    Python 启动脚本（可选）
echo   - config.json          配置文件
echo   - README.md            项目文档
echo.
echo 🚀 使用方法:
echo   1. 双击 AuroraShare.exe
echo   2. 等待自动打开浏览器
echo   3. 访问 http://localhost:8000
echo.
echo ⚠️  注意事项:
echo   - 首次启动可能较慢（10-30 秒）
echo   - 防火墙可能会提示，请选择"允许"
echo   - 关闭 EXE 窗口会停止服务
echo   - 默认存储路径：./shared_files
echo.
echo 🔧 修改配置:
echo   编辑 config.json 中的 base_dir 参数
echo.
echo 💡 提示:
echo   - 可以将整个 release 文件夹复制到任意位置
echo   - 可以创建桌面快捷方式方便使用
echo.
) > release\使用说明.txt

echo ✅ 文件整理完成
echo.

REM ==================== 完成提示 ====================
echo ╔══════════════════════════════════════════════════════════╗
echo ║                    🎉 打包完成！                         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 📦 发布包位置:
echo   .\release\AuroraShare.exe
echo.
echo 📁 文件大小:
for %%A in ("release\AuroraShare.exe") do echo   %%~zA 字节
echo.
echo ✅ 可以直接分发给用户了！
echo.
echo 💡 建议:
echo   1. 先测试运行 AuroraShare.exe
echo   2. 检查是否正常打开浏览器
echo   3. 测试上传下载功能
echo.

pause
