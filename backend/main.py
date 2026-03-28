# backend/main.py - 修改以支持打包
import os
import sys
import tempfile
import zipfile
import asyncio
import mimetypes
import json
import time

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends
from fastapi import status
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from file_manager import file_manager
from upload_manager import upload_manager
from backend.config import settings
from stats_manager import stats_manager, init_stats_manager
from fastapi.responses import FileResponse
import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel

mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/webm', '.webm')
mimetypes.add_type('video/ogg', '.ogv')
mimetypes.add_type('video/quicktime', '.mov')
mimetypes.add_type('video/x-msvideo', '.avi')
mimetypes.add_type('video/x-matroska', '.mkv')
# 确保 JavaScript 模块文件有正确的 MIME 类型
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/javascript', '.js')

app = FastAPI(title="AuroraShare · 极光共享")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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



# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("🚀 启动上传队列处理器...")
    await upload_manager.start_processor()
    print("✅ 上传队列处理器已启动")

    # 初始化统计管理器
    global stats_manager
    stats_manager = init_stats_manager(settings.base_dir)
    print("✅ 统计管理器已初始化")



# 添加数据模型
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: str = None
    username: str = None
    expire: int = None
    error: str = None


# 简单的会话存储（生产环境建议使用 Redis）
admin_sessions = {}

# 管理员配置（建议从环境变量读取）
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
ADMIN_SESSION_EXPIRE_HOURS = 24


# 清理过期会话的函数
def cleanup_expired_sessions():
    """清理过期的会话"""
    current_time = datetime.now()
    expired_tokens = [
        token for token, session in admin_sessions.items()
        if session.get('expire_time') and session['expire_time'] < current_time
    ]
    for token in expired_tokens:
        del admin_sessions[token]


@app.get("/debug/paths")
async def debug_paths():
    """调试路由：查看所有路径"""
    debug_info = {
        "frozen": getattr(sys, 'frozen', False),
        "meipass": getattr(sys, '_MEIPASS', None),
        "cwd": os.getcwd(),
        "frontend_paths": {}
    }

    # 检查各种可能的前端路径
    possible_paths = [
        get_resource_path('frontend'),
        os.path.join(os.getcwd(), 'frontend'),
        os.path.join(sys._MEIPASS, 'frontend') if getattr(sys, 'frozen', False) else None,
        os.path.join(os.path.dirname(sys.executable), 'frontend') if getattr(sys, 'frozen', False) else None,
    ]

    for path in possible_paths:
        if path and os.path.exists(path):
            debug_info["frontend_paths"][path] = {
                "exists": True,
                "contents": os.listdir(path)[:10]  # 只显示前10个文件
            }
        elif path:
            debug_info["frontend_paths"][path] = {"exists": False}

    return debug_info
# ==================== 管理员 API ====================

@app.post("/api/admin/login")
async def admin_login(login_data: LoginRequest):
    """
    管理员登录接口
    """
    try:
        # 验证用户名和密码
        if login_data.username == ADMIN_USERNAME and login_data.password == ADMIN_PASSWORD:
            # 生成会话 token
            token = secrets.token_urlsafe(32)
            expire_time = datetime.now() + timedelta(hours=ADMIN_SESSION_EXPIRE_HOURS)

            # 存储会话
            admin_sessions[token] = {
                "username": login_data.username,
                "expire_time": expire_time,
                "created_at": datetime.now(),
                "ip": "unknown"  # 可以记录IP，这里简化处理
            }

            # 清理过期会话
            cleanup_expired_sessions()

            print(f"[Auth] 管理员登录成功: {login_data.username}, token: {token[:10]}...")

            return {
                "success": True,
                "token": token,
                "username": login_data.username,
                "expire": ADMIN_SESSION_EXPIRE_HOURS * 3600  # 转换为秒
            }
        else:
            print(f"[Auth] 登录失败: 用户名或密码错误 - {login_data.username}")
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "用户名或密码错误"
                }
            )

    except Exception as e:
        print(f"[Auth] 登录异常: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.post("/api/admin/logout")
async def admin_logout(request: Request):
    """
    管理员登出接口
    """
    try:
        # 从请求头获取 token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            if token in admin_sessions:
                del admin_sessions[token]
                print(f"[Auth] 管理员登出成功, token: {token[:10]}...")

        return {"success": True}
    except Exception as e:
        print(f"[Auth] 登出异常: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/admin/verify")
async def verify_token(request: Request):
    """
    验证 token 是否有效
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {"valid": False, "error": "No token provided"}

        token = auth_header.split(' ')[1]

        # 清理过期会话
        cleanup_expired_sessions()

        session = admin_sessions.get(token)
        if not session:
            return {"valid": False, "error": "Invalid token"}

        # 检查是否过期
        if session.get('expire_time') and session['expire_time'] < datetime.now():
            del admin_sessions[token]
            return {"valid": False, "error": "Token expired"}

        return {
            "valid": True,
            "username": session['username'],
            "expire": int((session['expire_time'] - datetime.now()).total_seconds())
        }

    except Exception as e:
        print(f"[Auth] Token验证异常: {e}")
        return {"valid": False, "error": str(e)}


# 管理员认证依赖
async def require_admin(request: Request):
    """
    管理员认证依赖项
    """
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = auth_header.split(' ')[1]

    # 清理过期会话
    cleanup_expired_sessions()

    session = admin_sessions.get(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证信息",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # 检查是否过期
    if session.get('expire_time') and session['expire_time'] < datetime.now():
        del admin_sessions[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证信息已过期",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return session


# backend/main.py - 替换 get_admin_stats 函数

@app.get("/api/admin/stats")
async def get_admin_stats():
    """获取管理统计数据"""
    try:
        # 获取存储信息
        storage_info = await file_manager.get_storage_info()

        # 使用 stats_manager 获取统计信息
        today_uploads = stats_manager.get_today_uploads_count() if stats_manager else 0
        today_uploads_size = stats_manager.get_today_uploads_size() if stats_manager else 0
        trend_data = stats_manager.get_upload_trend(7) if stats_manager else []
        # 获取总上传数和总大小
        user_stats = stats_manager.get_user_stats() if stats_manager else {}
        total_uploads = user_stats.get('total_uploads', 0)
        total_uploads_size = user_stats.get('total_size', 0)

        return {
            "success": True,
            "data": {
                "total_files": storage_info.get('file_count', 0),
                "total_folders": storage_info.get('folder_count', 0),
                "total_size": storage_info.get('total', 0),
                "today_uploads": today_uploads,
                "today_uploads_size": today_uploads_size,
                "total_uploads": total_uploads,
                "total_uploads_size": total_uploads_size,
                "trend_data": trend_data,
                "storage": {
                    "total": storage_info.get('disk_total', 0),
                    "used": storage_info.get('disk_used', 0),
                    "free": storage_info.get('disk_free', 0),
                    "used_percent": storage_info.get('used_percent', 0)
                }
            }
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/admin/upload-logs")
async def get_upload_logs(
        start_date: str = None,
        end_date: str = None,
        limit: int = 100,
        auth: dict = Depends(require_admin)
):
    """获取上传日志（需要登录）"""
    try:
        logs = stats_manager._read_logs() if stats_manager else []

        # 日期过滤
        if start_date:
            logs = [log for log in logs if log.get('date') >= start_date]
        if end_date:
            logs = [log for log in logs if log.get('date') <= end_date]

        # 倒序排列（最新的在前）
        logs = list(reversed(logs))

        # 限制数量
        if limit > 0:
            logs = logs[:limit]

        return {
            "success": True,
            "data": {
                "logs": logs,
                "total": len(logs)
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.post("/api/admin/clean-logs")
async def clean_old_logs(days: int = 30, auth: dict = Depends(require_admin)):
    """清理旧日志（需要登录）"""
    try:
        if stats_manager:
            deleted = stats_manager.clear_old_logs(days)
            return {"success": True, "deleted": deleted}
        return {"success": True, "deleted": 0}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@app.get("/api/admin/logs")
async def admin_logs(
    page: int = 1,
    page_size: int = 20,
    keyword: str = "",
    level: str = "",
    auth: dict = Depends(require_admin)
):
    """
    获取系统日志（需要登录）
    """
    try:
        import os
        import re
        from backend.logger import get_log_dir
        
        # 获取日志目录
        log_dir = get_log_dir()
        
        # 读取所有日志文件
        log_files = []
        for filename in os.listdir(log_dir):
            if filename.startswith('aurorashare_') and filename.endswith('.log'):
                log_files.append(os.path.join(log_dir, filename))
        
        # 按日期排序，最新的在前
        log_files.sort(reverse=True)
        
        # 解析日志文件
        logs = []
        log_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(INFO|WARNING|ERROR|DEBUG)\] \[(.*?)\] (.*?):(\d+) - (.*)$')
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = log_pattern.match(line.strip())
                        if match:
                            log_time, log_level, log_name, log_file, log_line, log_content = match.groups()
                            
                            # 过滤条件
                            if keyword and keyword not in log_content:
                                continue
                            if level and log_level != level:
                                continue
                            
                            logs.append({
                                "time": log_time,
                                "level": log_level,
                                "content": log_content
                            })
            except Exception as e:
                print(f"Error reading log file {log_file}: {e}")
        
        # 分页
        total = len(logs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = logs[start:end]
        
        return {
            "success": True,
            "logs": paginated_logs,
            "total": total
        }
    except Exception as e:
        print(f"Error getting logs: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# 如果你需要 SSE 监控流
@app.get("/api/admin/monitor/stream")
async def admin_monitor_stream(request: Request, auth: dict = Depends(require_admin)):
    """
    管理员监控数据流（SSE）
    """

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break

                # 获取系统信息
                storage_info = await file_manager.get_storage_info()

                # 发送数据
                data = {
                    "timestamp": time.time(),
                    "storage": storage_info,
                    "active_sessions": len(admin_sessions)
                }

                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(5)
        except Exception as e:
            print(f"Monitor stream error: {e}")
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
        from urllib.parse import unquote

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
                'image/', 'video/', 'audio/', 'text/',
                'application/pdf', 'application/json'
            ]

            if mime_type and any(mime_type.startswith(t) for t in previewable_types):
                print(f"✅ 支持预览，返回文件")
                # 对于视频文件，添加额外的 headers 以支持播放
                headers = {}
                if mime_type and mime_type.startswith('video/'):
                    headers = {
                        "Accept-Ranges": "bytes",
                        "Cache-Control": "no-cache"
                    }

                return FileResponse(
                    full_path,
                    media_type=mime_type,
                    headers=headers
                )
            else:
                print(f"❌ 不支持预览的文件类型: {mime_type}")
                raise HTTPException(
                    status_code=415,
                    detail=f"Preview not supported for this file type: {mime_type or 'unknown'}"
                )

        # 下载模式
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


# 自定义静态文件处理，支持SPA路由回退
class SPAStaticFiles(StaticFiles):
    """支持SPA的静态文件处理，所有未匹配的路由都返回index.html"""
    async def get_response(self, path: str, scope):
        try:
            # 先尝试正常获取文件
            response = await super().get_response(path, scope)
            # 添加缓存控制头，防止浏览器缓存问题
            if path.endswith('.js') or path.endswith('.css'):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response
        except HTTPException as ex:
            # 如果是404错误，且请求的不是API路径，返回index.html
            if ex.status_code == 404:
                # 检查是否是API请求或文件请求
                if path.startswith('api/') or path.startswith('assets/'):
                    raise ex
                # 返回index.html让前端路由处理
                return await super().get_response("index.html", scope)
            raise ex

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



# 挂载前端静态文件（必须在API路由之后挂载）
frontend_path = get_resource_path("frontend")
if os.path.exists(frontend_path):
    print(f"[调试] 前端路径: {frontend_path}")
    # 使用自定义的SPAStaticFiles，支持前端路由
    app.mount("/", SPAStaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"[错误] 前端路径不存在: {frontend_path}")

