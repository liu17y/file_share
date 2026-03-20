@echo off
chcp 65001 >nul
cls

echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║      AuroraShare · 极光共享 - 一键打包工具              ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 📦 正在准备打包环境...
echo.

REM ==================== 检查 Python 环境 ====================
echo [1/7] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误：未检测到 Python 环境，请先安装 Python 3.8+
    echo 💡 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python 环境检测通过
python --version
echo.

REM ==================== 安装依赖 ====================
echo [2/7] 安装项目依赖...
if exist "backend\requirements.txt" (
    pip install -r backend\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ⚠️  未找到 requirements.txt，跳过依赖安装
)
echo.

REM ==================== 安装 PyInstaller ====================
echo [3/7] 安装打包工具 PyInstaller...
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo ❌ PyInstaller 安装失败
    pause
    exit /b 1
)
echo ✅ PyInstaller 安装完成
echo.

REM ==================== 创建临时目录 ====================
echo [4/7] 创建打包目录结构...
if not exist "dist_build" mkdir dist_build
if not exist "dist_build\backend" mkdir dist_build\backend
if not exist "dist_build\frontend" mkdir dist_build\frontend
echo ✅ 目录创建完成
echo.

REM ==================== 复制项目文件 ====================
echo [5/7] 复制项目文件到打包目录...

REM 复制后端文件
echo   📁 复制后端代码...
xcopy /E /I /Y backend\*.py dist_build\backend\
xcopy /E /I /Y backend\config.json dist_build\backend\ 2>nul
xcopy /E /I /Y backend\requirements.txt dist_build\backend\

REM 复制前端文件
echo   📁 复制前端代码...
xcopy /E /I /Y frontend\*.html dist_build\frontend\

REM 复制其他必要文件
echo   📁 复制启动脚本和文档...
copy run.py dist_build\ 2>nul
copy README.md dist_build\ 2>nul
copy LICENSE dist_build\ 2>nul

echo ✅ 文件复制完成
echo.

REM ==================== 创建启动器脚本 ====================
echo [6/7] 创建 Windows 启动器...

(
echo import sys
echo import os
echo from pathlib import Path
echo.
echo # 获取可执行文件所在目录
echo if getattr^(sys, 'frozen', False^):
echo     BASE_DIR = Path^(sys.executable^).parent
echo else:
echo     BASE_DIR = Path^(__file__^).parent.parent
echo.
echo # 添加 backend 到路径
echo backend_path = BASE_DIR / "backend"
echo if str^(backend_path^) not in sys.path:
echo     sys.path.insert^(0, str^(backend_path^)^)
echo.
echo # 切换工作目录
echo os.chdir^(backend_path^)
echo.
echo # 导入并运行主程序
echo from main import start_server
echo.
echo if __name__ == "__main__":
echo     print^("=" * 60^)
echo     print^("AuroraShare · 极光共享 启动中..."^)
echo     print^("=" * 60^)
echo     start_server^(^)
) > dist_build\launcher.pyw

echo ✅ 启动器创建完成
echo.

REM ==================== 开始打包 EXE ====================
echo [7/7] 开始打包为 EXE 文件...
echo.
echo 🔨 使用 PyInstaller 打包...
echo.

cd dist_build

REM 清理旧的打包文件
if exist "build" rmdir /s /q build
if exist "*.spec" del /q *.spec

REM 执行打包命令
pyinstaller ^
    --name "AuroraShare-极光共享" ^
    --onedir ^
    --windowed ^
    --icon=NONE ^
    --add-data "backend;backend" ^
    --add-data "frontend;frontend" ^
    --hidden-import fastapi ^
    --hidden-import uvicorn ^
    --hidden-import aiofiles ^
    --hidden-import asyncio ^
    --add-data "README.md;." ^
    --add-data "LICENSE;." ^
    launcher.pyw

if %errorlevel% neq 0 (
    echo.
    echo ❌ 打包失败！请查看上方错误信息
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo ✅ 打包成功完成！
echo.

REM ==================== 整理输出 ====================
echo ╔══════════════════════════════════════════════════════════╗
echo ║                    🎉 打包完成！                         ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 📦 可执行文件位置:
echo   dist_build\dist\AuroraShare-极光共享\AuroraShare-极光共享.exe
echo.
echo 📁 建议的操作:
echo   1. 测试运行：进入上述目录双击 EXE 运行
echo   2. 分发应用：将整个文件夹复制给其他用户
echo   3. 创建快捷方式：右键 EXE → 发送到 → 桌面快捷方式
echo.
echo 💡 使用说明:
echo   - 首次启动会自动打开浏览器访问 http://localhost:8000
echo   - 存储路径在 backend\config.json 中配置
echo   - 关闭 EXE 窗口会停止服务
echo.
echo ⚠️  注意事项:
echo   - 目标电脑需要安装 Python 运行时（可选）
echo   - 或者使用 --onefile 模式打包成单个 EXE（体积更大）
echo   - 防火墙可能会询问是否允许网络访问，请选择"允许"
echo.

pause
