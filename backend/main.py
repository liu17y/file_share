# backend/main.py - 修改以支持打包
import os
import sys
import tempfile
import zipfile
import asyncio
import mimetypes
import json
import time
import hashlib
import secrets
import psutil
from datetime import datetime, timedelta
from urllib.parse import quote, unquote
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from file_manager import file_manager
from upload_manager import upload_manager
from config import settings
from logger import get_logger, get_log_dir

logger = get_logger(__name__)

mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/webm', '.webm')
mimetypes.add_type('video/ogg', '.ogv')
mimetypes.add_type('video/quicktime', '.mov')
mimetypes.add_type('video/x-msvideo', '.avi')
mimetypes.add_type('video/x-matroska', '.mkv')

# 音频
mimetypes.add_type('audio/mpeg', '.mp3')
mimetypes.add_type('audio/wav', '.wav')
mimetypes.add_type('audio/flac', '.flac')
mimetypes.add_type('audio/ogg', '.ogg')
mimetypes.add_type('audio/aac', '.aac')
mimetypes.add_type('audio/x-m4a', '.m4a')

app = FastAPI(title="AuroraShare · 极光共享")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 管理员认证系统 ====================
# 简单的管理员账户存储（生产环境应使用数据库）
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()

# 活跃的 token 存储
active_tokens = {}

# 操作日志存储
operation_logs = []
MAX_LOGS = 1000


def generate_token():
    """生成随机 token"""
    return secrets.token_urlsafe(32)


def verify_token(authorization: str = Header(None)):
    """验证 token"""
    if not authorization:
        print("[Auth] 缺少 authorization header")
        raise HTTPException(status_code=401, detail="Missing authorization header")

    # 支持 Bearer token 格式
    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization

    print(f"[Auth] 收到 token: {token[:20]}...")
    print(f"[Auth] active_tokens 中存在的 token 数量: {len(active_tokens)}")
    
    if token not in active_tokens:
        print(f"[Auth] token 不在 active_tokens 中")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # 检查 token 是否过期（24小时）
    token_data = active_tokens[token]
    if datetime.now() - token_data["created_at"] > timedelta(hours=24):
        del active_tokens[token]
        print(f"[Auth] token 已过期")
        raise HTTPException(status_code=401, detail="Token expired")

    print(f"[Auth] token 验证通过: {token_data['username']}")
    return token_data


def add_operation_log(level: str, content: str, user: str = "system"):
    """添加操作日志"""
    log_entry = {
        "id": len(operation_logs) + 1,
        "time": datetime.now().isoformat(),
        "level": level,
        "content": content,
        "user": user
    }
    operation_logs.insert(0, log_entry)

    # 限制日志数量
    if len(operation_logs) > MAX_LOGS:
        operation_logs.pop()

    # 同时写入文件日志
    logger.info(f"[{level}] {content} (by {user})")


def get_resource_path(relative_path):
    """获取资源文件路径（支持打包）"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


# 从环境变量获取配置（支持打包）
if os.environ.get('AURORA_UPLOAD_DIR'):
    settings.base_dir = os.environ['AURORA_UPLOAD_DIR']

# 确保上传目录存在
os.makedirs(settings.base_dir, exist_ok=True)


# 健康检查
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "base_dir": settings.base_dir,
        "time": time.time(),
        "version": "1.0.0"
    }


# 获取文件列表
@app.get("/api/files")
async def get_files(path: str = ""):
    files = await file_manager.get_file_list(path)
    return {"files": files, "current_path": path}


# 创建文件夹
@app.post("/api/folders")
async def create_folder(request: Request):
    form_data = await request.form()
    path = form_data.get('path', '')
    name = form_data.get('name', '')

    if not name:
        return {"success": False, "error": "Folder name is required"}

    success = await file_manager.create_folder(path, name)
    return {"success": success}


# 批量删除
@app.delete("/api/items")
async def delete_items(paths: str = Form(...)):
    try:
        paths_list = json.loads(paths)
    except json.JSONDecodeError:
        paths_list = [paths]
    results = await file_manager.delete_items(paths_list)
    return results


# 获取存储信息
@app.get("/api/storage")
async def get_storage_info():
    info = await file_manager.get_storage_info()
    return info


# 更新存储路径
@app.post("/api/storage/path")
async def update_storage_path(new_path: str = Form(...)):
    success = await file_manager.update_storage_path(new_path)
    return {"success": success}


# 初始化上传
@app.post("/api/upload/init")
async def init_upload(request: Request):
    try:
        form_data = await request.form()

        file_id = form_data.get('file_id')
        file_name = form_data.get('file_name')
        file_size = form_data.get('file_size')
        target_path = form_data.get('target_path', '')
        total_chunks = form_data.get('total_chunks')

        if not file_id or not file_name or not file_size or not total_chunks:
            missing = []
            if not file_id: missing.append('file_id')
            if not file_name: missing.append('file_name')
            if not file_size: missing.append('file_size')
            if not total_chunks: missing.append('total_chunks')

            return JSONResponse(
                status_code=400,
                content={"error": f"Missing fields: {', '.join(missing)}"}
            )

        file_size_int = int(file_size)
        total_chunks_int = int(total_chunks)

        result = await upload_manager.init_upload(
            file_id, file_name, file_size_int, target_path, total_chunks_int
        )

        return result

    except Exception as e:
        print(f"Error processing upload init: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# 上传分块
@app.post("/api/upload/chunk")
async def upload_chunk(
        file_id: str = Form(...),
        chunk_index: int = Form(...),
        chunk_data: UploadFile = File(...)
):
    content = await chunk_data.read()
    result = await upload_manager.save_chunk(file_id, chunk_index, content)
    return result


# 获取上传状态
@app.get("/api/upload/status/{file_id}")
async def get_upload_status(file_id: str):
    status = await upload_manager.get_upload_status(file_id)
    if status:
        return status
    raise HTTPException(status_code=404, detail="Upload not found")


# 取消上传
@app.delete("/api/upload/{file_id}")
async def cancel_upload(file_id: str):
    success = await upload_manager.cancel_upload(file_id)
    return {"success": success}


# 下载/预览文件
@app.get("/api/files/{file_path:path}")
async def get_file(file_path: str, preview: bool = False):
    try:
        print(f"🔍 请求预览文件: {file_path}")
        print(f"📁 当前存储目录: {settings.base_dir}")

        # 解码URL编码的路径
        file_path = unquote(file_path)
        print(f"📄 解码后路径: {file_path}")

        # 构建完整路径
        if os.path.isabs(file_path):
            full_path = file_path
        else:
            file_path = file_path.replace('\\', '/')
            full_path = os.path.join(settings.base_dir, file_path)

        full_path = os.path.normpath(full_path)
        print(f"📂 完整路径: {full_path}")

        if not os.path.exists(full_path):
            print(f"❌ 文件不存在: {full_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

        if os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail="Cannot access directory")

        filename = os.path.basename(full_path)

        # 获取 MIME 类型
        mime_type, _ = mimetypes.guess_type(full_path)
        print(f"🎨 MIME类型: {mime_type}")

        # 预览模式
        if preview:
            # 支持预览的文件类型
            previewable_types = [
                'image/',  # 图片
                'video/',  # 视频
                'audio/',  # 音频
                'text/',  # 文本
                'application/pdf',  # PDF
                'application/json'  # JSON
            ]

            if mime_type and any(mime_type.startswith(t) for t in previewable_types):
                print(f"✅ 支持预览，返回文件")

                # 直接返回文件，不设置复杂的 Content-Disposition 头
                # 避免编码问题
                return FileResponse(
                    full_path,
                    media_type=mime_type,
                    headers={
                        "Accept-Ranges": "bytes",
                        "Cache-Control": "no-cache"
                    }
                )
            else:
                print(f"❌ 不支持预览的文件类型: {mime_type}")
                raise HTTPException(
                    status_code=415,
                    detail=f"Preview not supported for this file type: {mime_type or 'unknown'}"
                )

        # 下载模式 - 使用简单的 filename 参数
        return FileResponse(
            full_path,
            media_type='application/octet-stream',
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 文件访问错误: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# SSE 推送存储信息更新
@app.get("/api/storage/stream")
async def storage_stream(request: Request):
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                info = await file_manager.get_storage_info()
                yield f"data: {json.dumps(info)}\n\n"
                await asyncio.sleep(5)
        finally:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )


# 搜索接口
@app.get("/api/search")
async def search_files(query: str = "", path: str = ""):
    if not query or len(query.strip()) < 1:
        return {"files": [], "query": query, "path": path}

    results = await file_manager.search_files(query, path)
    return {"files": results, "query": query, "path": path}


# 移动/重命名接口
@app.post("/api/items/move")
async def move_items(request: Request):
    try:
        data = await request.json()

        if 'source' in data and 'target' in data:
            result = await file_manager.move_items(
                [{"source": data['source'], "target": data['target']}], ""
            )
            return result
        elif 'sources' in data and 'destination' in data:
            items = [{"source": s} for s in data['sources']]
            result = await file_manager.move_items(items, data['destination'])
            return result
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request format"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# 获取文件夹树
@app.get("/api/folder-tree")
async def get_folder_tree(path: str = ""):
    try:
        files = await file_manager.get_file_list(path)

        async def build_tree(current_path):
            items = await file_manager.get_file_list(current_path)
            folders = [f for f in items if f['is_dir']]

            result = []
            for folder in folders:
                node = {
                    "name": folder['name'],
                    "path": folder['path'],
                    "is_dir": True,
                    "children": await build_tree(folder['path'])
                }
                result.append(node)

            return result

        tree = await build_tree(path)
        return {"tree": tree}
    except Exception as e:
        return {"tree": []}


# 文件夹下载
@app.post("/api/download/folder")
async def download_folder(request: Request):
    try:
        data = await request.json()
        folder_path = data.get('path')

        if not folder_path:
            raise HTTPException(status_code=400, detail="Folder path is required")

        if os.path.isabs(folder_path):
            full_path = folder_path
        else:
            full_path = os.path.join(settings.base_dir, folder_path)

        full_path = os.path.normpath(full_path)

        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            raise HTTPException(status_code=404, detail="Folder not found")

        folder_name = os.path.basename(full_path) or "download"
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()

        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, os.path.dirname(full_path))
                    zipf.write(file_path, rel_path)

        return FileResponse(
            temp_zip.name,
            media_type='application/zip',
            filename=f"{folder_name}.zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 重命名文件/文件夹
@app.post("/api/items/rename")
async def rename_item(request: Request):
    """
    重命名文件或文件夹
    支持 JSON 和 FormData 两种格式
    """
    try:
        # 尝试获取 JSON 数据
        content_type = request.headers.get('content-type', '')
        if 'application/json' in content_type:
            data = await request.json()
            path = data.get('path')
            new_name = data.get('new_name')
        else:
            # 否则作为表单数据处理
            form_data = await request.form()
            path = form_data.get('path')
            new_name = form_data.get('new_name')

        if not path or not new_name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Missing path or new_name"}
            )

        # 调用重命名方法
        result = await file_manager.rename_item(path, new_name)

        # 检查结果并返回前端期望的格式
        if result.get('success') and len(result['success']) > 0:
            return {"success": True, "data": result['success'][0]}
        elif result.get('failed') and len(result['failed']) > 0:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": result['failed'][0].get('reason', 'Unknown error')}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Rename failed"}
            )

    except Exception as e:
        print(f"Rename error: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# 批量下载
@app.post("/api/download/batch")
async def download_batch(request: Request):
    try:
        data = await request.json()
        paths = data.get('paths', [])

        if not paths:
            raise HTTPException(status_code=400, detail="No paths provided")

        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()

        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for rel_path in paths:
                if os.path.isabs(rel_path):
                    full_path = rel_path
                else:
                    full_path = os.path.join(settings.base_dir, rel_path)

                full_path = os.path.normpath(full_path)

                if not os.path.exists(full_path):
                    continue

                if os.path.isdir(full_path):
                    for root, dirs, files in os.walk(full_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_file_path = os.path.relpath(file_path, settings.base_dir)
                            zipf.write(file_path, rel_file_path)
                else:
                    rel_file_path = os.path.relpath(full_path, settings.base_dir)
                    zipf.write(full_path, rel_file_path)

        return FileResponse(
            temp_zip.name,
            media_type='application/zip',
            filename="download.zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 管理页面
@app.get("/docliu", response_class=HTMLResponse)
async def admin_page():
    frontend_path = get_resource_path('frontend')
    admin_path = os.path.join(frontend_path, "admin.html")
    try:
        with open(admin_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return HTMLResponse(content=content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>")


# ==================== 管理员 API ====================
@app.post("/api/admin/login")
async def admin_login(request: Request):
    """管理员登录"""
    try:
        data = await request.json()
        username = data.get('username', '')
        password = data.get('password', '')

        # 验证用户名密码
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
            # 生成 token
            token = generate_token()
            active_tokens[token] = {
                "username": username,
                "created_at": datetime.now()
            }

            add_operation_log("INFO", f"管理员 {username} 登录成功", username)

            return {
                "success": True,
                "token": token,
                "admin": {
                    "username": username,
                    "role": "admin"
                }
            }
        else:
            add_operation_log("WARNING", f"登录失败: 用户名或密码错误 ({username})", username)
            raise HTTPException(status_code=401, detail="用户名或密码错误")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/logout")
async def admin_logout(authorization: str = Header(None)):
    """管理员登出"""
    try:
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
            if token in active_tokens:
                username = active_tokens[token]["username"]
                del active_tokens[token]
                add_operation_log("INFO", f"管理员 {username} 登出", username)

        return {"success": True}
    except Exception as e:
        logger.error(f"登出错误: {e}")
        return {"success": True}


@app.get("/api/admin/verify")
async def verify_admin_token(token_data: dict = Depends(verify_token)):
    """验证 token 是否有效"""
    return {"valid": True, "admin": token_data}


# ==================== 操作日志 API ====================
@app.get("/api/admin/logs")
async def get_logs(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    level: str = "",
    token_data: dict = Depends(verify_token)
):
    """获取操作日志"""
    try:
        # 过滤日志
        filtered_logs = operation_logs

        if keyword:
            filtered_logs = [log for log in filtered_logs if keyword.lower() in log['content'].lower()]

        if level:
            filtered_logs = [log for log in filtered_logs if log['level'] == level]

        # 分页
        total = len(filtered_logs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = filtered_logs[start:end]

        return {
            "logs": paginated_logs,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"获取日志错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统统计 API ====================
@app.get("/api/admin/stats")
async def get_system_stats(token_data: dict = Depends(verify_token)):
    """获取系统统计数据"""
    try:
        # 获取文件统计（使用 os.walk 遍历所有目录和文件）
        base_dir = file_manager._get_base_dir()
        total_files = 0
        total_folders = 0
        total_size = 0

        try:
            for root, dirs, files in os.walk(base_dir):
                # 跳过临时目录
                if '.temp_uploads' in root:
                    continue

                total_folders += len(dirs)
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(file_path)
                        total_size += size
                        total_files += 1
                    except (OSError, PermissionError):
                        pass
        except Exception as e:
            print(f"Error counting files: {e}")

        # 今日上传数量（模拟）
        def is_today(log_time):
            try:
                return datetime.fromisoformat(log_time).date() == datetime.now().date()
            except:
                return False

        today_uploads = len([log for log in operation_logs
                            if '上传' in log['content'] and
                            is_today(log.get('time', ''))])

        # 系统指标
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(settings.base_dir)

        # 生成趋势数据
        trend_data = []
        for i in range(6, -1, -1):
            date = datetime.now() - timedelta(days=i)
            def is_target_date(log_time):
                try:
                    return datetime.fromisoformat(log_time).date() == date.date()
                except:
                    return False
            trend_data.append({
                "date": f"{date.month}/{date.day}",
                "count": len([log for log in operation_logs
                             if is_target_date(log.get('time', ''))])
            })

        # 文件类型分布（模拟数据）
        type_distribution = [
            {"type": "图片", "count": total_files // 5},
            {"type": "视频", "count": total_files // 10},
            {"type": "文档", "count": total_files // 3},
            {"type": "其他", "count": total_files - (total_files // 5 + total_files // 10 + total_files // 3)}
        ]

        # 热门文件（模拟数据）
        hot_files = [
            {"name": "示例文件1.pdf", "downloads": 156, "size": 1024 * 1024 * 2},
            {"name": "示例文件2.jpg", "downloads": 89, "size": 1024 * 512},
            {"name": "示例文件3.mp4", "downloads": 67, "size": 1024 * 1024 * 50},
        ]

        return {
            "totalFiles": total_files,
            "totalFolders": total_folders,
            "totalSize": total_size,
            "todayUploads": today_uploads,
            "metrics": {
                "cpu": cpu_percent,
                "memory": memory.percent,
                "disk": (disk.used / disk.total * 100) if disk.total > 0 else 0
            },
            "trendData": trend_data,
            "typeDistribution": type_distribution,
            "hotFiles": hot_files,
            "analytics": {
                "totalViews": 12345,
                "totalDownloads": 5678,
                "totalTransfer": total_size * 2,
                "activeUsers": 42,
                "viewTrend": 12.5,
                "downloadTrend": 8.3,
                "transferTrend": 15.2,
                "userTrend": -2.1
            }
        }
    except Exception as e:
        logger.error(f"获取统计数据错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 实时监控 SSE ====================
@app.get("/api/admin/monitor/stream")
async def monitor_stream(request: Request):
    """SSE 实时监控系统资源"""
    # 从查询参数获取 token（SSE 不支持自定义 header）
    token = request.query_params.get('token', '')

    # 验证 token
    if not token or token not in active_tokens:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

    # 检查 token 是否过期
    token_data = active_tokens[token]
    if datetime.now() - token_data["created_at"] > timedelta(hours=24):
        del active_tokens[token]
        raise HTTPException(status_code=401, detail="Token expired")

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                # 获取系统指标
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage(settings.base_dir)

                data = {
                    "cpu": cpu_percent,
                    "memory": memory.percent,
                    "disk": (disk.used / disk.total * 100) if disk.total > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                }

                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"监控流错误: {e}")
        finally:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )


# ==================== 系统设置 API ====================
@app.get("/api/settings")
async def get_settings(token_data: dict = Depends(verify_token)):
    """获取系统设置"""
    try:
        return {
            "port": settings.port,
            "maxUploadSize": settings.max_upload_size_mb,
            "allowedExtensions": ','.join(settings.allowed_extensions) if hasattr(settings, 'allowed_extensions') else '.txt,.pdf,.png,.jpg,.jpeg,.gif,.mp4,.mp3,.doc,.docx,.zip',
            "autoOpenBrowser": getattr(settings, 'auto_open_browser', True),
            "debug": getattr(settings, 'debug', False)
        }
    except Exception as e:
        logger.error(f"获取设置错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def update_settings(request: Request, token_data: dict = Depends(verify_token)):
    """更新系统设置"""
    try:
        data = await request.json()

        # 更新配置
        if 'port' in data:
            settings.configured_port = int(data['port'])
        if 'maxUploadSize' in data:
            settings.max_upload_size_mb = int(data['maxUploadSize'])
        if 'autoOpenBrowser' in data:
            settings.auto_open_browser = bool(data['autoOpenBrowser'])
        if 'debug' in data:
            settings.debug = bool(data['debug'])

        # 保存到配置文件
        settings.save_config()

        add_operation_log("INFO", "系统设置已更新", token_data.get("username", "admin"))

        return {"success": True}
    except Exception as e:
        logger.error(f"更新设置错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 挂载前端静态文件

frontend_path = get_resource_path('frontend_dist')
if not os.path.exists(frontend_path):
    # 如果没有 frontend_legacy，使用原来的 frontend 目录
    frontend_path = get_resource_path('frontend')
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")