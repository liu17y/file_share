import sys
import os
import webbrowser
import time
from pathlib import Path

# 获取运行目录
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# 设置工作目录
os.chdir(BASE_DIR)

# 添加路径
backend_path = BASE_DIR / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

print("=" * 60)
print("AuroraShare · 极光共享")
print("=" * 60)
print()
print("🚀 服务启动中...")

# 延迟打开浏览器
def open_browser():
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:8000", new=2)
        print("✅ 已自动打开浏览器")
    except:
        print("⚠️  请手动访问 http://localhost:8000")

# 启动浏览器线程
import threading
browser_thread = threading.Threadtarget=open_browser)
browser_thread.daemon = True
browser_thread.start()

# 导入并运行
from main import start_server
print("💡 按 Ctrl+C 停止服务")
print()
start_server()
