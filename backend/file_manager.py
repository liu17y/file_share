import os
import shutil
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import mimetypes

from config import settings


class FileManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        os.makedirs(settings.base_dir, exist_ok=True)

    def _get_relative_path(self, full_path: str) -> str:
        """获取相对路径"""
        try:
            # 如果完整路径不在基础目录下，返回完整路径本身
            if not full_path.startswith(settings.base_dir):
                return full_path

            rel_path = os.path.relpath(full_path, settings.base_dir)
            return rel_path.replace('\\', '/')
        except ValueError:
            return full_path

    def _get_full_path(self, relative_path: str) -> str:
        """获取完整路径"""
        if not relative_path:
            return settings.base_dir

        # 如果相对路径已经是绝对路径（比如其他盘符），直接返回
        if os.path.isabs(relative_path):
            return relative_path

        if relative_path == '/' or relative_path == '\\':
            return settings.base_dir

        # 处理路径分隔符
        relative_path = relative_path.replace('\\', '/')

        # 安全地连接路径
        full_path = os.path.join(settings.base_dir, relative_path)

        # 规范化路径
        full_path = os.path.normpath(full_path)

        return full_path

    async def get_file_list(self, path: str = "") -> List[Dict[str, Any]]:
        """获取文件列表"""
        full_path = self._get_full_path(path)

        if not os.path.exists(full_path):
            print(f"Path does not exist: {full_path}")
            return []

        if not os.path.isdir(full_path):
            print(f"Path is not a directory: {full_path}")
            return []

        items = []
        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                try:
                    rel_path = self._get_relative_path(item_path)
                    stat = os.stat(item_path)

                    item_info = {
                        "name": item,
                        "path": rel_path.replace('\\', '/'),  # 统一使用正斜杠
                        "is_dir": os.path.isdir(item_path),
                        "size": stat.st_size if not os.path.isdir(item_path) else 0,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    }

                    if not item_info["is_dir"]:
                        mime_type, _ = mimetypes.guess_type(item_path)
                        item_info["mime_type"] = mime_type or "application/octet-stream"

                    items.append(item_info)
                except (OSError, PermissionError) as e:
                    print(f"Error accessing {item_path}: {e}")
                    continue

            # 排序：文件夹在前，文件在后，按名称排序
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        except Exception as e:
            print(f"Error listing directory {full_path}: {e}")

        return items

    async def create_folder(self, path: str, folder_name: str) -> bool:
        """创建文件夹"""
        try:
            print(f"Creating folder - path: '{path}', name: '{folder_name}'")

            # 处理路径
            # 如果 path 为空字符串、None、'/' 或 '\'，表示在根目录
            if not path or path in ['/', '\\']:
                full_path = os.path.join(settings.base_dir, folder_name)
            else:
                # 移除开头的 / 或 \
                clean_path = path.lstrip('/\\')
                full_path = os.path.join(settings.base_dir, clean_path, folder_name)

            print(f"Full path: {full_path}")

            # 确保目录存在
            os.makedirs(full_path, exist_ok=True)

            # 验证目录是否创建成功
            if os.path.exists(full_path) and os.path.isdir(full_path):
                print(f"Folder created successfully: {full_path}")
                return True
            else:
                print(f"Failed to verify folder creation: {full_path}")
                return False

        except Exception as e:
            print(f"Error creating folder: {e}")
            return False

    async def delete_items(self, paths: List[str]) -> Dict[str, Any]:
        """批量删除文件/文件夹"""
        results = {"success": [], "failed": []}

        for rel_path in paths:
            try:
                full_path = self._get_full_path(rel_path)
                if os.path.exists(full_path):
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    else:
                        os.remove(full_path)
                    results["success"].append(rel_path)
                    print(f"Deleted: {full_path}")
                else:
                    results["failed"].append({"path": rel_path, "reason": "not found"})
            except Exception as e:
                print(f"Error deleting {rel_path}: {e}")
                results["failed"].append({"path": rel_path, "reason": str(e)})

        return results

    async def get_storage_info(self) -> Dict[str, Any]:
        """获取存储空间信息（真实磁盘空间）"""
        try:
            # 获取磁盘总空间和可用空间
            disk_info = settings.get_disk_usage(settings.base_dir)

            # 计算当前目录下文件的实际占用空间
            dir_used = 0
            file_count = 0
            folder_count = 0

            for root, dirs, files in os.walk(settings.base_dir):
                # 跳过临时目录
                if '.temp_uploads' in root:
                    continue

                folder_count += len(dirs)
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        dir_used += size
                        file_count += 1
                    except (OSError, PermissionError):
                        pass

            # 磁盘总空间
            total = disk_info['total']
            # 磁盘剩余空间
            free = disk_info['free']
            # 磁盘已用空间
            disk_used = disk_info['used']

            # 当前目录已用空间
            used = dir_used

            return {
                "total": total,  # 磁盘总空间
                "used": used,  # 当前目录已用空间
                "free": free,  # 磁盘剩余空间
                "disk_total": total,  # 磁盘总空间
                "disk_free": free,  # 磁盘剩余空间
                "disk_used": disk_used,  # 磁盘已用空间
                "total_gb": round(total / (1024 ** 3), 2),
                "used_gb": round(used / (1024 ** 3), 2),
                "free_gb": round(free / (1024 ** 3), 2),
                "percentage": round((used / total) * 100, 2) if total > 0 else 0,
                "storage_path": settings.base_dir,
                "file_count": file_count,
                "folder_count": folder_count
            }

        except Exception as e:
            print(f"Error getting storage info: {e}")
            return {
                "total": 0,
                "used": 0,
                "free": 0,
                "disk_total": 0,
                "disk_free": 0,
                "disk_used": 0,
                "total_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "percentage": 0,
                "storage_path": settings.base_dir,
                "error": str(e)
            }

    async def update_storage_path(self, new_path: str) -> bool:
        """更新存储路径"""
        try:
            # 直接使用用户输入的路径，不做特殊处理
            abs_path = os.path.abspath(new_path)

            print(f"Attempting to update storage path to: {abs_path}")

            # 检查路径是否存在，如果不存在则创建
            if not os.path.exists(abs_path):
                try:
                    os.makedirs(abs_path, exist_ok=True)
                    print(f"Created directory: {abs_path}")
                except Exception as e:
                    print(f"Failed to create directory {abs_path}: {e}")
                    return False

            # 测试写入权限
            test_file = os.path.join(abs_path, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"Write test passed for: {abs_path}")
            except Exception as e:
                print(f"Write test failed for {abs_path}: {e}")
                return False

            # 更新设置
            if settings.set_base_dir(abs_path):
                # 更新上传管理器的临时目录
                from upload_manager import upload_manager
                upload_manager.temp_dir = os.path.join(abs_path, ".temp_uploads")
                os.makedirs(upload_manager.temp_dir, exist_ok=True)

                # 更新当前文件管理器的基本目录
                print(f"Storage path successfully updated to: {abs_path}")

                # 重新加载文件列表（回到根目录）
                return True
            return False

        except Exception as e:
            print(f"Error updating storage path: {e}")
            return False


file_manager = FileManager()