#!/usr/bin/env python
# run.py - 项目启动脚本（支持打包为exe，数据持久化）

import os
import sys
import webbrowser
import threading
import time
import socket


def get_base_path():
    """获取应用基础路径（支持 PyInstaller）"""
    if getattr(sys, 'frozen', False):
        # 打包后的路径 - 返回exe所在目录
        return os.path.dirname(sys.executable)
    else:
        # 开发环境路径
        return os.path.dirname(os.path.abspath(__file__))


def get_resource_path(relative_path):
    """获取资源文件路径（打包后的只读资源）"""
    if getattr(sys, 'frozen', False):
        # 打包后的资源路径 - 临时目录（只读）
        base_path = sys._MEIPASS
    else:
        # 开发环境路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_data_path(relative_path):
    """获取数据文件路径（可读写，保存在程序目录）"""
    base_path = get_base_path()
    return os.path.join(base_path, relative_path)


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
    import uvicorn
    import logging

    # 配置基础日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # 获取路径
        base_path = get_base_path()

        # 重要：数据目录（可读写）- 保存在程序所在目录
        data_dir = get_data_path('data')
        upload_dir = get_data_path('uploads')
        logs_dir = get_data_path('logs')
        config_dir = get_data_path('config')

        # 创建数据目录
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)
        os.makedirs(config_dir, exist_ok=True)

        logger.info("=" * 60)
        logger.info("AuroraShare 启动中...")
        logger.info(f"程序目录: {base_path}")
        logger.info(f"数据目录: {data_dir}")
        logger.info(f"上传目录: {upload_dir}")
        logger.info(f"日志目录: {logs_dir}")
        logger.info(f"配置目录: {config_dir}")
        logger.info("=" * 60)

        # 设置环境变量供backend使用（指向持久化目录）
        os.environ['AURORA_UPLOAD_DIR'] = upload_dir
        os.environ['AURORA_LOGS_DIR'] = logs_dir
        os.environ['AURORA_CONFIG_DIR'] = config_dir

        # 复制默认配置文件（如果不存在）
        default_config = get_resource_path(os.path.join('backend', 'config.json'))
        target_config = os.path.join(config_dir, 'config.json')

        if os.path.exists(default_config) and not os.path.exists(target_config):
            import shutil
            shutil.copy2(default_config, target_config)
            logger.info(f"已创建默认配置文件: {target_config}")

        # 设置前端路径（优先使用程序目录的前端，如果没有则使用临时目录）
        frontend_data_path = get_data_path('frontend')
        frontend_resource_path = get_resource_path('frontend')

        if os.path.exists(frontend_data_path):
            frontend_path = frontend_data_path
            logger.info(f"使用持久化前端: {frontend_path}")
        else:
            frontend_path = frontend_resource_path
            logger.info(f"使用内置前端: {frontend_path}")

        os.environ['AURORA_FRONTEND_PATH'] = frontend_path

        # 打印访问信息
        local_ip = get_local_ip()
        logger.info("=" * 60)
        logger.info("启动信息:")
        logger.info(f"  本地访问: http://localhost:8000")
        logger.info(f"  本机IP:   http://{local_ip}:8000")
        logger.info(f"  管理页面: http://localhost:8000/docliu")
        logger.info(f"  上传目录: {upload_dir}")
        logger.info(f"  日志目录: {logs_dir}")
        logger.info("=" * 60)

        # 自动打开浏览器
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open("http://localhost:8000")
                logger.info("浏览器已自动打开")
            except Exception as e:
                logger.error(f"打开浏览器失败: {e}")

        threading.Thread(target=open_browser, daemon=True).start()

        # 导入并启动应用
        sys.path.insert(0, get_resource_path('backend'))

        from backend.main import app

        # 启动服务器
        logger.info("启动 uvicorn 服务器...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )

    except KeyboardInterrupt:
        logger.info("\n服务已停止")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        input("\n按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()