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

REM 检查必要文件
echo [检查] 必要文件...
if not exist "run.py" (
    echo [错误] 缺少文件: run.py
    pause
    exit /b 1
)
if not exist "backend\main.py" (
    echo [错误] 缺少文件: backend\main.py
    pause
    exit /b 1
)
if not exist "backend\config.py" (
    echo [错误] 缺少文件: backend\config.py
    pause
    exit /b 1
)
if not exist "frontend\index.html" (
    echo [错误] 缺少文件: frontend\index.html
    pause
    exit /b 1
)
echo [√] 必要文件检查通过
echo.

REM 检查图标文件
set ICON_FLAG=
if exist "icon.ico" (
    echo [√] 找到图标文件: icon.ico
    set ICON_FLAG=--icon=icon.ico
) else (
    echo [!] 未找到图标文件 icon.ico，将使用默认图标
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

REM 创建配置文件模板（用于打包）
if not exist "config.json.template" (
    echo 创建配置文件模板...
    (
        echo {
        echo   "base_dir": "data/uploads",
        echo   "port": 8000,
        echo   "port_range_start": 8000,
        echo   "port_range_end": 8010,
        echo   "host": "0.0.0.0",
        echo   "max_upload_size_mb": 1024,
        echo   "auto_open_browser": true,
        echo   "debug": false,
        echo   "version": "1.0.0"
        echo }
    ) > config.json.template
)

REM 执行打包命令（修复了 --add-data 语法）
pyinstaller --onefile ^
    --name "AuroraShare" ^
    %ICON_FLAG% ^
    --add-data "frontend;frontend" ^
    --add-data "backend;backend" ^
    --add-data "config.json.template;." ^
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

    REM 获取文件大小
    for %%A in ("dist\AuroraShare.exe") do (
        set "size=%%~zA"
        set /a "size_mb=!size!/1048576"
        echo     文件大小: !size_mb! MB
    )
    echo.

    REM 创建 config 目录和配置文件
    echo 创建配置文件...
    if not exist "dist\config" mkdir dist\config
    if not exist "dist\config\config.json" (
        (
            echo {
            echo   "base_dir": "data/uploads",
            echo   "port": 8000,
            echo   "port_range_start": 8000,
            echo   "port_range_end": 8010,
            echo   "host": "0.0.0.0",
            echo   "max_upload_size_mb": 1024,
            echo   "auto_open_browser": true,
            echo   "debug": false,
            echo   "version": "1.0.0"
            echo }
        ) > dist\config\config.json
        echo [√] 已创建配置文件: config\config.json
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
        echo echo 访问地址: http://localhost:8000
        echo echo.
        echo echo 提示: 按 Ctrl+C 停止服务
        echo echo ========================================
        echo echo.
        echo AuroraShare.exe
        echo pause
    ) > "dist\启动AuroraShare.bat"
    echo [√] 已创建启动脚本: 启动AuroraShare.bat

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
    echo [√] 已创建快捷链接: AuroraShare.url

    REM 创建数据目录
    echo 创建数据目录...
    if not exist "dist\data" mkdir dist\data
    if not exist "dist\data\uploads" mkdir dist\data\uploads
    echo [√] 已创建数据目录: data\uploads\

    REM 创建日志目录
    echo 创建日志目录...
    if not exist "dist\logs" mkdir dist\logs
    echo [√] 已创建日志目录: logs\

    REM 创建版本信息文件
    echo 创建说明文件...
    (
        echo AuroraShare 文件共享系统 v1.0
        echo 构建日期: %date% %time%
        echo.
        echo ========================================
        echo 文件说明
        echo ========================================
        echo   AuroraShare.exe        - 主程序
        echo   启动AuroraShare.bat    - 启动脚本（双击运行）
        echo   AuroraShare.url        - 快速访问链接
        echo   config\                - 配置目录
        echo     └── config.json      - 配置文件（可修改）
        echo   data\                  - 数据目录
        echo     └── uploads\         - 上传文件存储位置
        echo   logs\                  - 日志目录（运行后自动创建）
        echo.
        echo ========================================
        echo 快速开始
        echo ========================================
        echo   1. 双击运行 "启动AuroraShare.bat" 或 "AuroraShare.exe"
        echo   2. 等待程序启动（首次启动较慢）
        echo   3. 自动打开浏览器访问 http://localhost:8000
        echo   4. 开始上传和共享文件
        echo.
        echo ========================================
        echo 配置说明
        echo ========================================
        echo   编辑 config\config.json 文件:
        echo   - base_dir: 文件存储目录（支持绝对路径或相对路径）
        echo   - port: 服务端口（默认8000）
        echo   - host: 监听地址（默认0.0.0.0）
        echo   - auto_open_browser: 是否自动打开浏览器
        echo   - max_upload_size_mb: 最大上传大小（MB）
        echo.
        echo   配置示例:
        echo   {"base_dir": "D:\\file-share", "port": 8080}
        echo.
        echo ========================================
        echo 故障排除
        echo ========================================
        echo   1. 如果无法启动，查看 logs 目录下的日志文件
        echo   2. 如果端口被占用，程序会自动寻找可用端口
        echo   3. 如果浏览器未自动打开，手动访问 http://localhost:端口号
        echo.
        echo ========================================
        echo 技术支持
        echo ========================================
        echo   GitHub: https://github.com/yourname/AuroraShare
        echo.
        echo © 2025 Aurora Team
    ) > "dist\README.txt"
    echo [√] 已创建说明文件: README.txt

    echo.
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
echo.
echo 📂 目录结构:
echo   dist\
echo   ├── AuroraShare.exe          # 主程序
echo   ├── 启动AuroraShare.bat      # 启动脚本
echo   ├── AuroraShare.url          # 快速访问链接
echo   ├── README.txt               # 使用说明
echo   ├── config\                  # 配置目录
echo   │   └── config.json          # 配置文件（可修改）
echo   ├── data\                    # 数据目录
echo   │   └── uploads\             # 上传文件存储
echo   └── logs\                    # 日志目录（运行后创建）
echo.
echo 💡 使用提示:
echo    1. 双击运行 dist\启动AuroraShare.bat
echo    2. 程序会自动打开浏览器访问 http://localhost:8000
echo    3. 修改配置: 编辑 dist\config\config.json
echo    4. 上传文件保存在 dist\data\uploads 目录
echo    5. 日志文件保存在 dist\logs 目录
echo.
echo ⚙️ 配置示例（编辑 config\config.json）:
echo    {
echo      "base_dir": "D:\\file-share",
echo      "port": 8080,
echo      "auto_open_browser": true
echo    }
echo.
echo ========================================
pause