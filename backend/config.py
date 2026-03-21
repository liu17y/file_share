import os
import sys
import json
import socket
from pathlib import Path


class Settings:
    def __init__(self):
        # 获取配置文件路径（支持打包）
        self.config_file = self._get_config_file_path()

        # 默认存储路径 - 使用程序目录下的 data/uploads
        self.default_base_dir = self._get_default_base_dir()

        # 默认端口范围
        self.default_port = 8000
        self.port_range_start = 8000
        self.port_range_end = 8010

        # 加载配置
        self.load_config()

        # 检查端口是否可用，如果被占用则自动寻找可用端口
        self.port = self._get_available_port()

        # 分块大小 (8MB)
        self.chunk_size = 8 * 1024 * 1024

        # 允许的文件类型
        self.allowed_extensions = {'.txt', '.pdf', '.png', '.jpg', '.jpeg', '.gif',
                                   '.mp4', '.mp3', '.doc', '.docx', '.xls', '.xlsx',
                                   '.zip', '.rar', '.7z', '.py', '.js', '.html', '.css'}

        # 打印配置信息
        print(f"\n[配置] ========== 配置信息 ==========")
        print(f"[配置] 运行模式: {'打包模式' if getattr(sys, 'frozen', False) else '开发模式'}")
        print(f"[配置] 程序目录: {self._get_base_path()}")
        print(f"[配置] 配置文件: {self.config_file}")
        print(f"[配置] 存储目录: {self.base_dir}")
        print(f"[配置] 使用端口: {self.port}")
        print(f"[配置] ================================\n")

    def _get_base_path(self):
        """获取程序基础路径"""
        if getattr(sys, 'frozen', False):
            # 打包模式：exe所在目录
            return os.path.dirname(sys.executable)
        else:
            # 开发模式：项目根目录（file-share/）
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _get_config_file_path(self):
        """获取配置文件路径"""
        base_path = self._get_base_path()
        is_frozen = getattr(sys, 'frozen', False)

        print(f"[调试] 运行模式: {'打包模式' if is_frozen else '开发模式'}")
        print(f"[调试] 基础路径: {base_path}")

        if is_frozen:
            # 打包模式：只从 config 文件夹查找 config.json
            config_paths = [
                os.path.join(base_path, 'config', 'config.json'),  # 程序目录/config/config.json
                os.path.join(base_path, 'config.json'),  # 程序目录/config.json（备用）
            ]
        else:
            # 开发模式：优先使用 backend/config.json
            config_paths = [
                os.path.join(os.path.dirname(__file__), 'config.json'),  # backend/config.json
                os.path.join(base_path, 'config', 'config.json'),  # 项目根目录/config/config.json
                os.path.join(base_path, 'config.json'),  # 项目根目录/config.json
            ]

        print(f"[调试] 查找配置文件:")
        for path in config_paths:
            print(f"  检查: {path}")
            if os.path.exists(path):
                print(f"[配置] ✓ 找到配置文件: {path}")
                return path

        # 如果都不存在，返回默认路径
        if is_frozen:
            # 打包模式：默认在 config 目录创建
            default_path = os.path.join(base_path, 'config', 'config.json')
            # 确保 config 目录存在
            os.makedirs(os.path.dirname(default_path), exist_ok=True)
        else:
            # 开发模式：默认在 backend 目录创建
            default_path = os.path.join(os.path.dirname(__file__), 'config.json')

        print(f"[配置] 未找到配置文件，将使用默认路径: {default_path}")
        return default_path

    def _get_default_base_dir(self):
        """获取默认存储路径"""
        base_path = self._get_base_path()
        is_frozen = getattr(sys, 'frozen', False)

        if is_frozen:
            # 打包模式：使用程序目录下的 data/uploads
            default_dir = os.path.join(base_path, 'data', 'uploads')
        else:
            # 开发模式：使用项目根目录下的 uploads
            default_dir = os.path.join(base_path, 'uploads')

        # 如果环境变量指定了上传目录，优先使用
        if os.environ.get('AURORA_UPLOAD_DIR'):
            default_dir = os.environ['AURORA_UPLOAD_DIR']

        return default_dir

    def _resolve_path(self, path):
        """解析路径，支持相对路径和绝对路径"""
        if not path:
            return self.default_base_dir

        # 如果是绝对路径，直接返回
        if os.path.isabs(path):
            return path

        # 如果是相对路径，相对于程序目录
        base_path = self._get_base_path()
        resolved_path = os.path.join(base_path, path)

        # 规范化路径
        resolved_path = os.path.normpath(resolved_path)

        return resolved_path

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                    print(f"[调试] 配置文件内容: {config}")

                    # 获取配置的存储路径
                    configured_dir = config.get('base_dir')

                    if configured_dir:
                        # 解析路径（支持相对路径和绝对路径）
                        self.base_dir = self._resolve_path(configured_dir)
                        print(f"[配置] 使用配置的存储目录: {configured_dir} -> {self.base_dir}")
                    else:
                        self.base_dir = self.default_base_dir
                        print(f"[配置] 未配置 base_dir，使用默认: {self.base_dir}")

                    # 获取配置的端口
                    self.configured_port = config.get('port', self.default_port)

                    # 获取端口范围（可选）
                    self.port_range_start = config.get('port_range_start', self.default_port)
                    self.port_range_end = config.get('port_range_end', self.default_port + 10)

                    # 获取其他配置
                    self.host = config.get('host', '0.0.0.0')
                    self.max_upload_size_mb = config.get('max_upload_size_mb', 1024)
                    self.auto_open_browser = config.get('auto_open_browser', True)
                    self.debug = config.get('debug', False)

            else:
                # 没有配置文件，使用默认值
                print(f"[配置] 配置文件不存在，使用默认配置")
                self.base_dir = self.default_base_dir
                self.configured_port = self.default_port
                self.host = '0.0.0.0'
                self.max_upload_size_mb = 1024
                self.auto_open_browser = True
                self.debug = False

                # 创建默认配置文件
                self._create_default_config()

        except Exception as e:
            print(f"[错误] 加载配置失败: {e}")
            import traceback
            traceback.print_exc()
            self.base_dir = self.default_base_dir
            self.configured_port = self.default_port
            self.host = '0.0.0.0'
            self.max_upload_size_mb = 1024
            self.auto_open_browser = True
            self.debug = False

        # 确保目录存在
        try:
            os.makedirs(self.base_dir, exist_ok=True)
            print(f"[配置] 存储目录已准备: {self.base_dir}")

            # 测试写入权限
            test_file = os.path.join(self.base_dir, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"[配置] 写入权限测试通过")
            except Exception as e:
                print(f"[警告] 写入权限测试失败: {e}")

        except Exception as e:
            print(f"[错误] 无法创建存储目录: {e}")

    def _create_default_config(self):
        """创建默认配置文件"""
        try:
            is_frozen = getattr(sys, 'frozen', False)
            base_path = self._get_base_path()

            # 设置默认的 base_dir（相对路径）
            if is_frozen:
                default_base_dir = "data/uploads"
            else:
                default_base_dir = "uploads"

            default_config = {
                "base_dir": default_base_dir,
                "port": self.default_port,
                "port_range_start": 8000,
                "port_range_end": 8010,
                "host": "0.0.0.0",
                "max_upload_size_mb": 1024,
                "auto_open_browser": True,
                "debug": False,
                "version": "1.0.0"
            }

            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            print(f"[配置] 已创建默认配置文件: {self.config_file}")
            print(f"[配置] 默认配置: {default_config}")

        except Exception as e:
            print(f"[错误] 创建默认配置文件失败: {e}")

    def _is_port_available(self, port):
        """检查端口是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', port))
            sock.close()
            return True
        except socket.error:
            return False
        except Exception:
            return False

    def _find_available_port(self, start_port, end_port=None):
        """寻找可用端口"""
        if end_port is None:
            if self._is_port_available(start_port):
                return start_port
            end_port = start_port + 10

        print(f"[端口] 正在寻找可用端口 ({start_port}-{end_port})...")

        for port in range(start_port, end_port + 1):
            if self._is_port_available(port):
                print(f"[端口] 找到可用端口: {port}")
                return port

        print(f"[端口] 端口范围 {start_port}-{end_port} 内无可用端口")
        return None

    def _get_available_port(self):
        """获取可用端口"""
        configured_port = getattr(self, 'configured_port', self.default_port)

        # 首先检查配置的端口是否可用
        if self._is_port_available(configured_port):
            return configured_port

        # 如果配置的端口被占用，寻找可用端口
        print(f"[端口] 配置端口 {configured_port} 已被占用，正在寻找备用端口...")

        start_port = configured_port + 1
        end_port = self.port_range_end

        if configured_port >= self.port_range_end:
            end_port = configured_port + 10

        available_port = self._find_available_port(start_port, end_port)

        if available_port is None:
            available_port = self._find_available_port(self.default_port, self.default_port + 10)

        if available_port is None:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('0.0.0.0', 0))
                available_port = sock.getsockname()[1]
                sock.close()
                print(f"[端口] 系统分配端口: {available_port}")
            except:
                print(f"[端口] 错误: 无法获取可用端口")
                return configured_port

        if available_port != configured_port:
            self._save_port_to_config(available_port)

        return available_port

    def _save_port_to_config(self, new_port):
        """保存新端口到配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}

            config['port'] = new_port

            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"[配置] 已将端口 {new_port} 保存到配置文件: {self.config_file}")
        except Exception as e:
            print(f"[警告] 保存端口到配置文件失败: {e}")

    def save_config(self):
        """保存配置到文件"""
        try:
            base_path = self._get_base_path()
            is_frozen = getattr(sys, 'frozen', False)

            # 设置保存的 base_dir（使用相对路径）
            try:
                if is_frozen:
                    # 打包模式：使用相对于程序目录的路径
                    rel_path = os.path.relpath(self.base_dir, base_path)
                    if not rel_path.startswith('..'):
                        save_base_dir = rel_path
                    else:
                        save_base_dir = self.base_dir
                else:
                    # 开发模式：使用相对于项目根目录的路径
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    rel_path = os.path.relpath(self.base_dir, project_root)
                    if not rel_path.startswith('..'):
                        save_base_dir = rel_path
                    else:
                        save_base_dir = self.base_dir
            except:
                save_base_dir = self.base_dir

            config = {
                'base_dir': save_base_dir,
                'port': self.port,
                'port_range_start': self.port_range_start,
                'port_range_end': self.port_range_end,
                'host': getattr(self, 'host', '0.0.0.0'),
                'max_upload_size_mb': getattr(self, 'max_upload_size_mb', 1024),
                'auto_open_browser': getattr(self, 'auto_open_browser', True),
                'debug': getattr(self, 'debug', False),
                'version': '1.0.0'
            }

            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"[配置] 配置已保存: {self.config_file}")
            return True
        except Exception as e:
            print(f"[错误] 保存配置失败: {e}")
            return False

    def set_base_dir(self, path):
        """设置存储路径"""
        try:
            # 解析路径
            abs_path = self._resolve_path(path)

            print(f"[配置] 设置存储目录: {abs_path}")

            # 创建目录
            os.makedirs(abs_path, exist_ok=True)

            # 测试写入权限
            test_file = os.path.join(abs_path, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"[配置] 写入权限测试通过")
            except Exception as e:
                print(f"[错误] 写入权限测试失败: {e}")
                return False

            # 更新路径
            self.base_dir = abs_path

            # 保存配置
            if self.save_config():
                print(f"[配置] 存储目录已更新: {abs_path}")
                return True
            else:
                print("[错误] 保存配置失败")
                return False

        except Exception as e:
            print(f"[错误] 设置存储目录失败: {e}")
            return False

    def get_disk_usage(self, path):
        """获取磁盘使用情况"""
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                free_bytes = ctypes.c_ulonglong(0)
                total_bytes = ctypes.c_ulonglong(0)

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


# 全局设置实例
settings = Settings()