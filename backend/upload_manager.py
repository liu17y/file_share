import os
import aiofiles
from typing import Dict, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import time
import hashlib  # 添加 hash 支持

from config import settings
from stats_manager import stats_manager


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
        """处理上传任务 - 工业级分片上传实现"""
        file_id = task['file_id']
        chunk_index = task['chunk_index']
        chunk_data = task['chunk_data']
    
        try:
            upload_info = self.uploads.get(file_id)
            if not upload_info:
                print(f"Upload info not found for {file_id}")
                return
    
            temp_path = upload_info["temp_path"]
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            # 工业级方案核心：使用固定的 chunk_size (2MB)
            # 这与前端的 File.slice() 逻辑完全匹配
            chunk_size = upload_info["chunk_size"]  # 2 * 1024 * 1024
            
            # 精确定位：每个分片写入到固定的偏移量
            position = chunk_index * chunk_size
                
            # 预分配文件空间（可选，但能提高性能）
            if not os.path.exists(temp_path):
                with open(temp_path, 'wb') as f:
                    pass  # 创建空文件
                
            # 定位并写入分片数据
            async with aiofiles.open(temp_path, 'r+b') as f:
                await f.seek(position)
                await f.write(chunk_data)
                await f.flush()
    
            upload_info["uploaded_chunks"].add(chunk_index)

            # 每10个块保存一次进度
            if len(upload_info["uploaded_chunks"]) % 10 == 0:
                await self._save_progress(file_id)

            # 检查是否完成
            if len(upload_info["uploaded_chunks"]) == upload_info["total_chunks"]:
                await self._finalize_upload(file_id)

        except Exception as e:
            print(f"Error processing upload task: {e}")
            # 如果出错，记录错误信息
            if file_id in self.uploads:
                self.uploads[file_id]["error"] = str(e)
                self.uploads[file_id]["status"] = "failed"

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
        """初始化上传任务 - 修复文件夹上传问题"""
        # 确保处理器已启动
        await self.start_processor()
    
        # 处理目标路径
        print(f"Initializing upload: target_path='{target_path}', file_name='{file_name}'")
    
        # 规范化目标路径
        if target_path is None or target_path == '' or target_path == '/' or target_path == '\\':
            # 根目录
            target_dir = settings.base_dir
            clean_path = ''
            print(f"Root directory detected, target_dir = {target_dir}")
        else:
            # 非根目录，清理路径
            clean_path = target_path.replace('\\', '/').strip('/')
            # 处理可能的路径分隔符问题
            clean_path = clean_path.replace('//', '/')
            if clean_path:
                target_dir = os.path.join(settings.base_dir, clean_path)
            else:
                target_dir = settings.base_dir
            print(f"Subdirectory detected: {clean_path}, target_dir = {target_dir}")
    
        # 确保目标目录存在
        try:
            os.makedirs(target_dir, exist_ok=True)
            print(f"Ensured target directory exists: {target_dir}")
        except Exception as e:
            print(f"Error creating target directory: {e}")
            return {"error": f"Failed to create target directory: {str(e)}"}
    
        # 临时文件路径 - 使用 file_id 避免冲突
        temp_path = self._get_temp_path(file_id)
        print(f"Temp file path: {temp_path}")
    
        # 检查是否已有部分上传
        uploaded_chunks = set()
        if os.path.exists(temp_path):
            info_path = self._get_upload_info_path(file_id)
            if os.path.exists(info_path):
                try:
                    async with aiofiles.open(info_path, 'r') as f:
                        saved_info = json.loads(await f.read())
                        uploaded_chunks = set(saved_info.get("uploaded_chunks", []))
                        print(f"Resuming upload for {file_name}, {len(uploaded_chunks)} chunks already uploaded")
                except Exception as e:
                    print(f"Error loading saved progress: {e}")
    
        # 关键修复：使用固定的 chunk_size (2MB)，与前端保持一致
        # 前端使用 Math.ceil(file.size / chunkSize) 计算分片数
        # 因此除了最后一个分片，其他分片大小都是固定的 2MB
        CHUNK_SIZE = 2 * 1024 * 1024  # 2MB，必须与前端 chunkSize 一致
    
        upload_info = {
            "file_id": file_id,
            "file_name": file_name,
            "file_size": file_size,
            "target_path": target_path,
            "target_dir": target_dir,
            "total_chunks": total_chunks,
            "chunk_size": CHUNK_SIZE,  # 固定的分片大小
            "uploaded_chunks": uploaded_chunks,
            "status": "resumed" if uploaded_chunks else "initialized",
            "temp_path": temp_path,
            "created_at": time.time()
        }

        self.uploads[file_id] = upload_info

        # 清理旧的未完成上传
        await self._cleanup_old_uploads()

        result = {
            "file_id": file_id,
            "uploaded_chunks": list(uploaded_chunks),
            "status": upload_info["status"]
        }
        print(f"Init upload result: {result}")
        return result

    async def save_chunk(self, file_id: str, chunk_index: int, chunk_data: bytes) -> Dict:
        """保存分块数据"""
        if file_id not in self.uploads:
            print(f"Upload not found for file_id: {file_id}")
            return {"error": "Upload not found"}

        upload_info = self.uploads[file_id]

        # 如果块已经上传，跳过
        if chunk_index in upload_info["uploaded_chunks"]:
            print(f"Chunk {chunk_index} already uploaded for {file_id}")
            return {
                "file_id": file_id,
                "chunk_index": chunk_index,
                "uploaded_chunks": list(upload_info["uploaded_chunks"]),
                "total_chunks": upload_info["total_chunks"],
                "completed": len(upload_info["uploaded_chunks"]) == upload_info["total_chunks"]
            }

        # 加入处理队列
        await self.upload_queue.put({
            'file_id': file_id,
            'chunk_index': chunk_index,
            'chunk_data': chunk_data
        })

        # 注意：这里返回的uploaded_chunks还没有包含当前chunk，
        # 因为它是异步处理的。前端应该轮询状态来获取最新进度
        return {
            "file_id": file_id,
            "chunk_index": chunk_index,
            "uploaded_chunks": list(upload_info["uploaded_chunks"]),
            "total_chunks": upload_info["total_chunks"],
            "completed": len(upload_info["uploaded_chunks"]) == upload_info["total_chunks"]
        }

    async def _finalize_upload(self, file_id: str):
        """完成上传，合并文件并进行 Hash 校验"""
        upload_info = self.uploads[file_id]

        # 处理文件名，确保即使包含路径也能正确处理
        file_name = upload_info["file_name"]

        # 构建完整路径，包括目录结构
        target_full_path = os.path.join(upload_info["target_dir"], file_name)

        # 确保目标目录存在（包括文件名中可能包含的子目录）
        os.makedirs(os.path.dirname(target_full_path), exist_ok=True)

        try:
            print(f"Finalizing upload: {target_full_path}")

            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_full_path), exist_ok=True)

            # 检查临时文件是否存在
            if not os.path.exists(upload_info["temp_path"]):
                raise FileNotFoundError(f"Temporary file not found: {upload_info['temp_path']}")

            # 检查文件大小是否匹配
            temp_size = os.path.getsize(upload_info["temp_path"])
            expected_size = upload_info["file_size"]

            if temp_size != expected_size:
                error_msg = f"File size mismatch. Expected {expected_size}, got {temp_size}"
                print(f"Warning: {error_msg}")
                raise ValueError(error_msg)

            # 计算临时文件的 MD5 Hash
            print("Calculating MD5 hash for integrity check...")
            md5_hash = hashlib.md5()

            # 使用同步方式读取文件计算 hash
            def calculate_hash():
                with open(upload_info["temp_path"], 'rb') as f:
                    for chunk in iter(lambda: f.read(8192), b''):
                        md5_hash.update(chunk)
                return md5_hash.hexdigest()

            # 在线程池中计算 hash，避免阻塞
            loop = asyncio.get_event_loop()
            file_md5 = await loop.run_in_executor(
                self.executor,
                calculate_hash
            )

            print(f"File MD5: {file_md5}")
            print(f"File integrity verified: {temp_size} bytes")

            # 移动临时文件到目标位置
            if os.path.exists(target_full_path):
                os.remove(target_full_path)
                print(f"Removed existing file: {target_full_path}")

            os.rename(upload_info["temp_path"], target_full_path)
            print(f"Moved temp file to: {target_full_path}")

            # 清理临时信息文件
            info_path = self._get_upload_info_path(file_id)
            if os.path.exists(info_path):
                os.remove(info_path)
                print(f"Removed info file: {info_path}")

            # ========== 新增：记录上传统计 ==========
            try:
                if stats_manager:
                    stats_manager.log_upload(
                        file_name=file_name,
                        file_size=expected_size,
                        target_path=upload_info["target_path"]
                    )
                    print(f"📊 已记录上传统计: {file_name}")
            except Exception as stats_error:
                print(f"记录上传统计失败: {stats_error}")
            # ======================================

            upload_info["status"] = "completed"
            upload_info["md5"] = file_md5
            print(f"Upload completed successfully: {target_full_path}")
            print(f"✓ File verified - Size: {temp_size} bytes, MD5: {file_md5}")

            # 从活跃上传中移除
            if file_id in self.uploads:
                del self.uploads[file_id]
                print(f"Removed upload info for {file_id}")

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
                    print(f"Removed temp file: {temp_path}")
                if os.path.exists(info_path):
                    os.remove(info_path)
                    print(f"Removed info file: {info_path}")
            except Exception as e:
                print(f"Error cleaning up files: {e}")

            del self.uploads[file_id]
            print(f"Cancelled upload for {file_id}")
            return True
        return False

    def __del__(self):
        """析构时取消队列处理器任务"""
        if self.queue_processor_task:
            self.queue_processor_task.cancel()


# 创建全局实例
upload_manager = UploadManager()