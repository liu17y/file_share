import os
import json
import shutil
from pathlib import Path


class Settings:
    def __init__(self):
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        # 默认存储路径 - 使用用户目录下的共享文件夹
        self.default_base_dir = os.path.join(os.path.expanduser("~"), "FileShare")
        # 加载配置
        self.load_config()
        # 不再限制最大空间，使用实际磁盘空间
        self.chunk_size = 8 * 1024 * 1024  # 分块大小 (8MB)
        # 允许的文件类型
        self.allowed_extensions = {'.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif',
                                   '.mp4', '.mp3', '.doc', '.docx', '.xls', '.xlsx',
                                   '.zip', '.rar', '.7z', '.py', '.js', '.html', '.css'}

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.base_dir = config.get('base_dir', self.default_base_dir)
            else:
                self.base_dir = self.default_base_dir
        except Exception as e:
            print(f"Error loading config: {e}")
            self.base_dir = self.default_base_dir

        # 确保目录存在
        os.makedirs(self.base_dir, exist_ok=True)

    def save_config(self):
        """保存配置到文件"""
        try:
            config = {
                'base_dir': self.base_dir
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_disk_usage(self, path):
        """获取磁盘使用情况"""
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)

                # 获取磁盘根路径
                drive = os.path.splitdrive(path)[0] + '\\'
                if not drive or drive == '\\':
                    drive = None

                if drive:
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        ctypes.c_wchar_p(drive),
                        None,
                        ctypes.pointer(total_bytes),
                        ctypes.pointer(free_bytes)
                    )
                else:
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        None,
                        None,
                        ctypes.pointer(total_bytes),
                        ctypes.pointer(free_bytes)
                    )

                total = total_bytes.value
                free = free_bytes.value
                used = total - free

            else:  # Linux/Mac
                stat = os.statvfs(path)
                total = stat.f_blocks * stat.f_frsize
                free = stat.f_bavail * stat.f_frsize
                used = total - free

            return {
                'total': total,
                'used': used,
                'free': free
            }
        except Exception as e:
            print(f"Error getting disk usage: {e}")
            return {
                'total': 0,
                'used': 0,
                'free': 0
            }

    def set_base_dir(self, path):
        """设置存储路径"""
        try:
            # 确保路径是绝对路径
            abs_path = os.path.abspath(path)

            print(f"Setting base dir to: {abs_path}")

            # 创建目录（如果不存在）
            os.makedirs(abs_path, exist_ok=True)

            # 测试写入权限
            test_file = os.path.join(abs_path, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"Write test passed for: {abs_path}")
            except Exception as e:
                print(f"Write test failed: {e}")
                return False

            # 更新路径
            self.base_dir = abs_path

            # 保存配置
            if self.save_config():
                print(f"Configuration saved with base_dir: {abs_path}")
                return True
            else:
                print("Failed to save configuration")
                return False

        except Exception as e:
            print(f"Error setting base dir: {e}")
            return False


settings = Settings()