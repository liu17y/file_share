import os
import aiofiles
from typing import Dict, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import time

from config import settings


class UploadManager:
    def __init__(self):
        self.uploads: Dict[str, Dict] = {}  # 存储上传任务信息
        self.temp_dir = os.path.join(settings.base_dir, ".temp_uploads")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.upload_queue = asyncio.Queue()
        self.queue_processor_task = None
        # 不在init中启动，改为延迟启动

    def _get_temp_path(self, file_id: str) -> str:
        """获取临时文件路径"""
        return os.path.join(self.temp_dir, f"{file_id}.part")

    def _get_upload_info_path(self, file_id: str) -> str:
        """获取上传信息文件路径"""
        return os.path.join(self.temp_dir, f"{file_id}.json")

    async def start_processor(self):
        """启动上传队列处理器 - 需要异步调用"""
        if self.queue_processor_task is None:
            self.queue_processor_task = asyncio.create_task(self._process_queue())
            print("Upload queue processor started")

    async def _process_queue(self):
        """处理队列的后台任务"""
        while True:
            try:
                # 从队列获取任务，设置超时避免阻塞
                try:
                    task = await asyncio.wait_for(self.upload_queue.get(), timeout=1.0)
                    await self._process_upload_task(task)
                    self.upload_queue.task_done()
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Queue processor error: {e}")
                    await asyncio.sleep(1)
            except Exception as e:
                print(f"Fatal queue processor error: {e}")
                break

    async def _process_upload_task(self, task):
        """处理上传任务"""
        file_id = task['file_id']
        chunk_index = task['chunk_index']
        chunk_data = task['chunk_data']

        try:
            upload_info = self.uploads.get(file_id)
            if not upload_info:
                print(f"Upload info not found for {file_id}")
                return

            # 异步写入分块
            async with aiofiles.open(upload_info["temp_path"], 'ab') as f:
                await f.write(chunk_data)

            upload_info["uploaded_chunks"].add(chunk_index)

            # 每10个块保存一次进度
            if len(upload_info["uploaded_chunks"]) % 10 == 0:
                await self._save_progress(file_id)

            # 检查是否完成
            if len(upload_info["uploaded_chunks"]) == upload_info["total_chunks"]:
                await self._finalize_upload(file_id)

        except Exception as e:
            print(f"Error processing upload task: {e}")

    async def _save_progress(self, file_id: str):
        """保存上传进度"""
        upload_info = self.uploads.get(file_id)
        if not upload_info:
            return

        info_path = self._get_upload_info_path(file_id)
        try:
            async with aiofiles.open(info_path, 'w') as f:
                await f.write(json.dumps({
                    "uploaded_chunks": list(upload_info["uploaded_chunks"])
                }))
        except Exception as e:
            print(f"Error saving progress: {e}")

    async def init_upload(self, file_id: str, file_name: str, file_size: int,
                          target_path: str, total_chunks: int) -> Dict:
        """初始化上传任务"""
        # 确保处理器已启动
        await self.start_processor()

        # 确保目标路径正确
        if target_path == '/' or target_path == '\\' or target_path == '':
            target_dir = settings.base_dir
        else:
            # 清理路径
            clean_path = target_path.replace('\\', '/')
            target_dir = os.path.join(settings.base_dir, clean_path)

        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)

        upload_info = {
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "target_path": target_path,
            "target_dir": target_dir,
            "total_chunks": total_chunks,
            "uploaded_chunks": set(),
            "status": "initialized",
            "temp_path": self._get_temp_path(file_id),
            "created_at": time.time()
        }

        self.uploads[file_id] = upload_info

        # 检查是否已有部分上传
        if os.path.exists(upload_info["temp_path"]):
            info_path = self._get_upload_info_path(file_id)
            if os.path.exists(info_path):
                try:
                    async with aiofiles.open(info_path, 'r') as f:
                        saved_info = json.loads(await f.read())
                        upload_info["uploaded_chunks"] = set(saved_info.get("uploaded_chunks", []))
                        upload_info["status"] = "resumed"
                        print(f"Resuming upload for {file_name}, {len(upload_info['uploaded_chunks'])} chunks already uploaded")
                except Exception as e:
                    print(f"Error loading saved progress: {e}")

        # 清理旧的未完成上传
        await self._cleanup_old_uploads()

        return {
            "file_id": file_id,
            "uploaded_chunks": list(upload_info["uploaded_chunks"]),
            "status": upload_info["status"]
        }

    async def save_chunk(self, file_id: str, chunk_index: int, chunk_data: bytes) -> Dict:
        """保存分块数据"""
        if file_id not in self.uploads:
            return {"error": "Upload not found"}

        upload_info = self.uploads[file_id]

        # 如果块已经上传，跳过
        if chunk_index in upload_info["uploaded_chunks"]:
            return {
                "file_id": file_id,
                "chunk_index": chunk_index,
                "uploaded_chunks": len(upload_info["uploaded_chunks"]),
                "total_chunks": upload_info["total_chunks"],
                "completed": len(upload_info["uploaded_chunks"]) == upload_info["total_chunks"]
            }

        # 加入处理队列
        await self.upload_queue.put({
            'file_id': file_id,
            'chunk_index': chunk_index,
            'chunk_data': chunk_data
        })

        return {
            "file_id": file_id,
            "chunk_index": chunk_index,
            "uploaded_chunks": len(upload_info["uploaded_chunks"]),
            "total_chunks": upload_info["total_chunks"],
            "completed": len(upload_info["uploaded_chunks"]) == upload_info["total_chunks"]
        }

    async def _finalize_upload(self, file_id: str):
        """完成上传，合并文件"""
        upload_info = self.uploads[file_id]
        target_full_path = os.path.join(upload_info["target_dir"], upload_info["file_name"])

        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_full_path), exist_ok=True)

            # 移动临时文件到目标位置
            if os.path.exists(target_full_path):
                os.remove(target_full_path)
            os.rename(upload_info["temp_path"], target_full_path)

            # 清理临时文件
            info_path = self._get_upload_info_path(file_id)
            if os.path.exists(info_path):
                os.remove(info_path)

            upload_info["status"] = "completed"

            # 从活跃上传中移除
            if file_id in self.uploads:
                del self.uploads[file_id]

            print(f"Upload completed: {target_full_path}")

        except Exception as e:
            upload_info["status"] = "failed"
            upload_info["error"] = str(e)
            print(f"Error finalizing upload: {e}")

    async def _cleanup_old_uploads(self, max_age_hours=24):
        """清理旧的未完成上传"""
        current_time = time.time()
        to_delete = []

        for file_id, info in self.uploads.items():
            if current_time - info.get("created_at", 0) > max_age_hours * 3600:
                to_delete.append(file_id)

        for file_id in to_delete:
            await self.cancel_upload(file_id)

    async def get_upload_status(self, file_id: str) -> Optional[Dict]:
        """获取上传状态"""
        if file_id in self.uploads:
            info = self.uploads[file_id]
            return {
                "file_id": file_id,
                "uploaded_chunks": list(info["uploaded_chunks"]),
                "total_chunks": info["total_chunks"],
                "status": info["status"]
            }
        return None

    async def cancel_upload(self, file_id: str) -> bool:
        """取消上传"""
        if file_id in self.uploads:
            temp_path = self._get_temp_path(file_id)
            info_path = self._get_upload_info_path(file_id)

            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(info_path):
                    os.remove(info_path)
            except Exception as e:
                print(f"Error cleaning up files: {e}")

            del self.uploads[file_id]
            return True
        return False

    def __del__(self):
        """析构时取消队列处理器任务"""
        if self.queue_processor_task:
            self.queue_processor_task.cancel()


# 创建全局实例
upload_manager = UploadManager()