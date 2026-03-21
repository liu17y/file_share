# backend/main.py - 修改以支持打包

import os
import sys
import tempfile
import zipfile
import asyncio
import socket
import mimetypes
import json
import time
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import aiofiles

from file_manager import file_manager
from upload_manager import upload_manager
from config import settings

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
    if os.path.isabs(file_path):
        full_path = file_path
    else:
        full_path = os.path.join(settings.base_dir, file_path)

    full_path = os.path.normpath(full_path)

    if not os.path.exists(full_path) or os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    filename = os.path.basename(full_path)

    if preview:
        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type and mime_type.startswith(('image/', 'video/', 'audio/', 'text/', 'application/pdf')):
            return FileResponse(full_path, media_type=mime_type)

    return FileResponse(
        full_path,
        media_type='application/octet-stream',
        filename=filename
    )


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


# 挂载前端静态文件
frontend_path = get_resource_path('frontend')
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")