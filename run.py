#!/usr/bin/env python
# run.py - 项目启动脚本

import os
import sys
import subprocess
import webbrowser
import time


def main():
    """启动文件共享系统"""

    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(current_dir, "backend")

    # 检查Python环境
    python_executable = sys.executable

    # 检查依赖
    print("检查依赖...")
    requirements_file = os.path.join(backend_dir, "requirements.txt")

#     # 创建requirements.txt如果不存在
#     if not os.path.exists(requirements_file):
#         with open(requirements_file, 'w') as f:
#             f.write("""fastapi==0.104.1
# uvicorn==0.24.0
# aiofiles==23.2.1
# python-multipart==0.0.6
# """)
#
#     try:
#         subprocess.run([python_executable, "-m", "pip", "install", "-r", requirements_file],
#                        check=True, capture_output=True)
#         print("依赖安装完成")
#     except subprocess.CalledProcessError as e:
#         print("安装依赖失败，请手动安装:")
#         print(f"pip install -r {requirements_file}")
#         print(e.stderr.decode() if e.stderr else "")

    # 启动后端服务
    print("\n启动文件共享服务...")
    print("访问地址: http://localhost:8000")
    print("访问地址: http://`${ipa}`:8000")
    print("按 Ctrl+C 停止服务\n")

    # 延迟打开浏览器
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

    # 启动服务
    os.chdir(backend_dir)
    subprocess.run([python_executable, "-m", "uvicorn", "main:app",
                    "--host", "0.0.0.0", "--port", "8000", "--reload"])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n服务已停止")
        sys.exit(0)