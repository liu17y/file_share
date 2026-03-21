# backend/logger.py
import os
import sys
import logging
import logging.handlers
from datetime import datetime


class Logger:
    """日志管理器"""

    def __init__(self):
        self.log_dir = self._get_log_dir()
        self._setup_logging()

    def _get_log_dir(self):
        """获取日志目录"""
        # 优先使用环境变量
        if os.environ.get('AURORA_LOGS_DIR'):
            return os.environ['AURORA_LOGS_DIR']

        # 打包模式：使用程序所在目录的 logs
        if getattr(sys, 'frozen', False):
            log_dir = os.path.join(os.path.dirname(sys.executable), 'logs')
        else:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')

        os.makedirs(log_dir, exist_ok=True)
        return log_dir

    def _setup_logging(self):
        """配置日志系统"""
        # 日志文件路径
        log_file = os.path.join(self.log_dir, f'aurorashare_{datetime.now().strftime("%Y%m%d")}.log')
        error_log_file = os.path.join(self.log_dir, f'aurorashare_error_{datetime.now().strftime("%Y%m%d")}.log')

        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 日志格式
        log_format = '%(asctime)s [%(levelname)s] [%(name)s] %(filename)s:%(lineno)d - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter(log_format, date_format)

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # 文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # 错误日志文件处理器
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        # 减少第三方库的日志
        logging.getLogger('uvicorn').setLevel(logging.WARNING)
        logging.getLogger('fastapi').setLevel(logging.WARNING)

        self.logger = logging.getLogger('AuroraShare')
        self.logger.info("=" * 60)
        self.logger.info(f"日志系统初始化完成，日志目录: {self.log_dir}")
        self.logger.info("=" * 60)

    def get_logger(self, name=None):
        """获取日志器"""
        if name:
            return logging.getLogger(f'AuroraShare.{name}')
        return self.logger


# 全局日志实例
logger_instance = Logger()


def get_logger(name=None):
    return logger_instance.get_logger(name)


def get_log_dir():
    return logger_instance.log_dir