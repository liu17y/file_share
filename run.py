#!/usr/bin/env python
# run.py - 项目启动脚本（支持动态端口）

import os
import sys
import webbrowser
import threading
import time
import socket
import json
import logging


def get_base_path():
    """获取应用基础路径（支持 PyInstaller）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(relative_path):
    """获取资源文件路径（打包后的只读资源）"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def setup_logging(logs_dir):
    """配置日志"""
    log_file = os.path.join(logs_dir, f'aurorashare.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def get_local_ip():
    """获取本机IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    """主函数"""
    try:
        # 获取基础路径
        base_path = get_base_path()

        # 添加backend目录到路径
        backend_path = get_resource_path('backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        # 导入配置
        from config import settings

        # 创建数据目录
        upload_dir = settings.base_dir
        logs_dir = os.path.join(base_path, 'logs')
        config_dir = os.path.join(base_path, 'config')

        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(config_dir, exist_ok=True)

        # 配置日志
        logger = setup_logging(logs_dir)

        logger.info("=" * 60)
        logger.info("AuroraShare 启动中...")
        logger.info(f"程序目录: {base_path}")
        logger.info(f"配置文件: {settings.config_file}")
        logger.info(f"上传目录: {upload_dir}")
        logger.info(f"日志目录: {logs_dir}")
        logger.info(f"使用端口: {settings.port}")

        # 设置环境变量
        os.environ['AURORA_UPLOAD_DIR'] = upload_dir
        os.environ['AURORA_LOGS_DIR'] = logs_dir
        os.environ['AURORA_CONFIG_DIR'] = config_dir
        os.environ['AURORA_PORT'] = str(settings.port)

        # 获取前端路径
        external_frontend = os.path.join(base_path, 'frontend_dist')
        if os.path.exists(external_frontend):
            frontend_path = external_frontend
            logger.info(f"使用外部前端: {frontend_path}")
        else:
            frontend_path = get_resource_path('frontend')
            logger.info(f"使用内置前端: {frontend_path}")

        os.environ['AURORA_FRONTEND_PATH'] = frontend_path

        # 打印启动信息
        local_ip = get_local_ip()
        port = settings.port

        logger.info("=" * 60)
        logger.info("启动信息:")
        logger.info(f"  本地访问: http://localhost:{port}")
        logger.info(f"  本机IP:   http://{local_ip}:{port}")
        logger.info(f"  管理页面: http://localhost:{port}/docliu")
        logger.info("=" * 60)

        # 自动打开浏览器
        auto_open = getattr(settings, 'auto_open_browser', True)
        if auto_open:
            def open_browser():
                time.sleep(2)
                try:
                    webbrowser.open(f"http://localhost:{port}")
                    logger.info("浏览器已自动打开")
                except Exception as e:
                    logger.error(f"打开浏览器失败: {e}")

            threading.Thread(target=open_browser, daemon=True).start()

        # 导入并启动应用
        from backend.main import app

        import uvicorn

        # 启动服务器
        logger.info(f"启动 uvicorn 服务器 (端口: {port})...")
        uvicorn.run(
            app,
            host=settings.host if hasattr(settings, 'host') else "0.0.0.0",
            port=port,
            reload=False,
            log_level="info"
        )

    except KeyboardInterrupt:
        print("\n服务已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()