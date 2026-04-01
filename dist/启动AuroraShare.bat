@echo off
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
