import os
import shutil
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import mimetypes

from backend.config import settings


class FileManager:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        # 不在 __init__ 中固定 base_dir，改为在需要时动态获取

    def _get_base_dir(self):
        """获取当前基础目录（每次动态获取）"""
        # 确保目录存在
        os.makedirs(settings.base_dir, exist_ok=True)
        return settings.base_dir

    def _get_relative_path(self, full_path: str) -> str:
        """获取相对路径"""
        try:
            base_dir = self._get_base_dir()
            # 如果完整路径不在基础目录下，返回完整路径本身
            if not full_path.startswith(base_dir):
                return full_path

            rel_path = os.path.relpath(full_path, base_dir)
            return rel_path.replace('\\', '/')
        except ValueError:
            return full_path

    def _get_full_path(self, relative_path: str) -> str:
        """获取完整路径"""
        base_dir = self._get_base_dir()

        if not relative_path:
            return base_dir

        # 如果相对路径已经是绝对路径（比如其他盘符），直接返回
        if os.path.isabs(relative_path):
            return relative_path

        if relative_path == '/' or relative_path == '\\':
            return base_dir

        # 处理路径分隔符
        relative_path = relative_path.replace('\\', '/')

        # 安全地连接路径
        full_path = os.path.join(base_dir, relative_path)

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
                # 过滤掉隐藏文件和文件夹（以 . 开头）
                if item.startswith('.'):
                    continue

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

    async def search_files(self, query: str, start_path: str = "") -> List[Dict[str, Any]]:
        """
        递归搜索文件
        - query: 搜索关键词
        - start_path: 起始路径
        """
        full_path = self._get_full_path(start_path)

        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return []

        results = []
        query_lower = query.lower()

        try:
            # 使用 os.walk 遍历目录
            for root, dirs, files in os.walk(full_path):
                # 过滤掉隐藏目录（以 . 开头）
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                # 检查当前目录名是否匹配
                dir_name = os.path.basename(root)
                if query_lower in dir_name.lower():
                    try:
                        rel_path = self._get_relative_path(root)
                        stat = os.stat(root)
                        results.append({
                            "name": dir_name,
                            "path": rel_path.replace('\\', '/'),
                            "is_dir": True,
                            "size": 0,
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "match_type": "folder",
                            "match_path": rel_path.replace('\\', '/')
                        })
                    except:
                        pass

                # 检查文件
                for file in files:
                    if query_lower in file.lower():
                        file_path = os.path.join(root, file)
                        try:
                            rel_path = self._get_relative_path(file_path)
                            stat = os.stat(file_path)
                            mime_type, _ = mimetypes.guess_type(file_path)

                            results.append({
                                "name": file,
                                "path": rel_path.replace('\\', '/'),
                                "is_dir": False,
                                "size": stat.st_size,
                                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                "mime_type": mime_type or "application/octet-stream",
                                "match_type": "file",
                                "match_path": rel_path.replace('\\', '/')
                            })
                        except:
                            pass

                # 限制结果数量，避免太多
                if len(results) >= 200:
                    break

        except Exception as e:
            print(f"Search error: {e}")

        # 排序：文件夹优先，然后按名称
        results.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        return results

    async def create_folder(self, path: str, folder_name: str) -> bool:
        """创建文件夹"""
        try:
            base_dir = self._get_base_dir()
            print(f"Creating folder - path: '{path}', name: '{folder_name}'")

            # 处理路径
            if not path or path in ['/', '\\']:
                full_path = os.path.join(base_dir, folder_name)
            else:
                clean_path = path.lstrip('/\\')
                full_path = os.path.join(base_dir, clean_path, folder_name)

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
            base_dir = self._get_base_dir()

            # 获取磁盘总空间和可用空间
            disk_info = settings.get_disk_usage(base_dir)

            # 计算当前目录下文件的实际占用空间
            dir_used = 0
            file_count = 0
            folder_count = 0

            for root, dirs, files in os.walk(base_dir):
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
                "storage_path": base_dir,
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

                print(f"Storage path successfully updated to: {abs_path}")
                return True
            return False

        except Exception as e:
            print(f"Error updating storage path: {e}")
            return False

    async def move_items(self, items: List[Dict[str, str]], destination: str) -> Dict[str, Any]:
        """
        移动或重命名文件/文件夹
        items: [{"source": "相对路径", "target": "目标路径或新名称"}]
        destination: 目标文件夹路径（如果是移动到文件夹）
        """
        results = {"success": [], "failed": []}
        base_dir = self._get_base_dir()

        for item in items:
            try:
                source_path = item.get('source')
                target_name = item.get('target')

                if not source_path:
                    results["failed"].append({"path": "未知", "reason": "缺少源路径"})
                    continue

                full_source = self._get_full_path(source_path)

                if not os.path.exists(full_source):
                    results["failed"].append({"path": source_path, "reason": "源文件不存在"})
                    continue

                # 确定目标路径
                if target_name:
                    # 重命名：target 是新名称
                    target_dir = os.path.dirname(full_source)
                    full_target = os.path.join(target_dir, target_name)
                else:
                    # 移动到文件夹：destination 是目标文件夹
                    if destination is None:
                        results["failed"].append({"path": source_path, "reason": "目标路径为空"})
                        continue

                    # 处理目标路径（允许空字符串表示根目录）
                    if destination == '':
                        # 目标为根目录
                        dest_full = base_dir
                    else:
                        dest_full = self._get_full_path(destination)

                    # 确保目标目录存在
                    if not os.path.exists(dest_full):
                        os.makedirs(dest_full, exist_ok=True)

                    base_name = os.path.basename(full_source)
                    full_target = os.path.join(dest_full, base_name)

                # 安全检查：不能移动到自身或子文件夹
                if os.path.exists(full_target):
                    if os.path.samefile(full_source, full_target):
                        results["failed"].append({"path": source_path, "reason": "源和目标相同"})
                        continue

                    # 检查是否将父文件夹移动到子文件夹
                    if os.path.isdir(full_source) and full_target.startswith(full_source + os.sep):
                        results["failed"].append({"path": source_path, "reason": "不能将文件夹移动到其子文件夹中"})
                        continue

                # 如果目标已存在，添加数字后缀
                if os.path.exists(full_target):
                    base, ext = os.path.splitext(os.path.basename(full_target))
                    counter = 1
                    target_dir = os.path.dirname(full_target)
                    while os.path.exists(os.path.join(target_dir, f"{base} ({counter}){ext}")):
                        counter += 1
                    full_target = os.path.join(target_dir, f"{base} ({counter}){ext}")

                # 执行移动/重命名
                shutil.move(full_source, full_target)

                rel_target = self._get_relative_path(full_target)
                results["success"].append({
                    "source": source_path,
                    "target": rel_target.replace('\\', '/'),
                    "is_dir": os.path.isdir(full_target)
                })
                print(f"Moved: {full_source} -> {full_target}")

            except Exception as e:
                print(f"Error moving {item.get('source')}: {e}")
                results["failed"].append({
                    "path": item.get('source'),
                    "reason": str(e)
                })

        return results

    async def rename_item(self, path: str, new_name: str) -> Dict[str, Any]:
        """重命名文件或文件夹（单个）"""
        return await self.move_items([{"source": path, "target": new_name}], "")


file_manager = FileManager()