@echo off
chcp 65001 >nul
title AuroraShare 打包工具
color 0A

echo ========================================
echo   AuroraShare 打包工具 v1.0
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    echo.
    pause
    exit /b 1
)

echo [√] Python 环境检查通过
python --version
echo.

REM 检查图标文件
set ICON_FLAG=
if exist "icon.ico" (
    echo [√] 找到图标文件: icon.ico
    set ICON_FLAG=--icon=icon.ico
) else (
    echo [!] 未找到图标文件 icon.ico，将使用默认图标
    echo     提示：将你的图标文件命名为 icon.ico 放在当前目录
    echo.
)

echo.
echo ========================================
echo [1/5] 安装 PyInstaller...
echo ========================================
pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [错误] PyInstaller 安装失败
    pause
    exit /b 1
)
echo [√] PyInstaller 安装完成
echo.

echo ========================================
echo [2/5] 安装项目依赖...
echo ========================================
if exist "backend\requirements.txt" (
    pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo [警告] 部分依赖安装失败，继续打包...
    )
) else (
    echo [!] 未找到 requirements.txt，跳过依赖安装
)
echo [√] 依赖检查完成
echo.

echo ========================================
echo [3/5] 清理旧打包文件...
echo ========================================
if exist "dist" (
    echo 删除 dist 目录...
    rmdir /s /q dist
)
if exist "build" (
    echo 删除 build 目录...
    rmdir /s /q build
)
if exist "*.spec" (
    echo 删除 spec 文件...
    del /q *.spec
)
echo [√] 清理完成
echo.

echo ========================================
echo [4/5] 开始打包程序...
echo ========================================
echo 正在打包，请稍候...
echo.

REM 执行打包命令
pyinstaller --onefile ^
    --name "AuroraShare" ^
    %ICON_FLAG% ^
    --add-data "frontend;frontend" ^
    --add-data "backend;backend" ^
    --add-data "backend\config.json;backend" ^
    --hidden-import uvicorn ^
    --hidden-import uvicorn.loops ^
    --hidden-import uvicorn.loops.auto ^
    --hidden-import uvicorn.protocols ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.websockets ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    --hidden-import aiofiles ^
    --hidden-import watchfiles ^
    --hidden-import python_multipart ^
    --hidden-import backend.logger ^
    --collect-all fastapi ^
    --collect-all starlette ^
    --collect-all pydantic ^
    --clean ^
    --noconfirm ^
    run.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo   [错误] 打包失败！
    echo ========================================
    echo.
    echo 请检查错误信息，常见问题：
    echo 1. Python 版本过低（需要 3.7+）
    echo 2. 缺少必要的依赖包
    echo 3. 路径中包含中文字符
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo [5/5] 打包完成，整理文件...
echo ========================================

REM 检查生成的文件
if exist "dist\AuroraShare.exe" (
    echo [√] 主程序生成成功
    for %%A in ("dist\AuroraShare.exe") do (
        set /a size=%%~zA / 1048576
        echo     文件大小: !size! MB
    )

    REM 创建启动脚本
    echo 创建启动脚本...
    (
        echo @echo off
        echo chcp 65001 ^>nul
        echo title AuroraShare
        echo echo ========================================
        echo echo   AuroraShare 文件共享系统
        echo echo ========================================
        echo echo.
        echo echo 正在启动服务器...
        echo echo.
        echo AuroraShare.exe
        echo pause
    ) > "dist\启动AuroraShare.bat"

    REM 创建快速访问链接
    echo 创建快速访问链接...
    (
        echo [InternetShortcut]
        echo URL=http://localhost:8000
        echo IDList=
        echo HotKey=0
        echo IconFile=AuroraShare.exe
        echo IconIndex=0
    ) > "dist\AuroraShare.url"

    REM 创建版本信息文件
    echo 创建版本信息文件...
    (
        echo AuroraShare 版本信息
        echo ========================================
        echo.
        echo 版本: 1.0.0
        echo 构建日期: %date% %time%
        echo.
        echo 主要功能:
        echo - 断点续传
        echo - 文件夹上传
        echo - 文件预览
        echo - 日志记录
        echo.
        echo 使用说明:
        echo 1. 双击运行 AuroraShare.exe
        echo 2. 程序会自动打开浏览器
        echo 3. 上传的文件保存在 data/uploads 目录
        echo 4. 日志文件保存在 logs 目录
        echo 5. 配置文件保存在 config 目录
        echo.
        echo 系统要求:
        echo - Windows 7 及以上
        echo - 建议 2GB 内存
        echo - 建议 100MB 磁盘空间
        echo.
        echo 技术支持: https://github.com/yourname/AuroraShare
    ) > "dist\README.txt"

    echo [√] 辅助文件创建完成
) else (
    echo [错误] 未找到生成的可执行文件
    pause
    exit /b 1
)

echo.
echo ========================================
echo   打包成功！ ✨
echo ========================================
echo.
echo 📦 输出目录: %cd%\dist
echo 📄 主程序: dist\AuroraShare.exe
echo 🚀 启动脚本: dist\启动AuroraShare.bat
echo 🔗 快捷访问: dist\AuroraShare.url
echo 📖 使用说明: dist\README.txt
echo.
echo 📁 运行后会自动创建以下目录:
echo    data\          - 上传文件存储
echo    logs\          - 日志文件
echo    config\        - 配置文件
echo.
echo 💡 使用提示:
echo    1. 双击运行 dist\AuroraShare.exe
echo    2. 程序会自动打开浏览器访问 http://localhost:8000
echo    3. 首次启动可能需要几秒钟初始化
echo    4. 日志文件在 logs\aurorashare_*.log
echo.
echo ========================================
pause