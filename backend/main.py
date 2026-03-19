import tempfile
import zipfile

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import asyncio
import socket
from typing import List, Optional
import aiofiles
import mimetypes
import time

from file_manager import file_manager
from upload_manager import upload_manager
from config import settings

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="File Share System")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保上传目录存在
os.makedirs(settings.base_dir, exist_ok=True)


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("Starting upload queue processor...")
    await upload_manager.start_processor()
    print("Upload queue processor started")


# 健康检查
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "base_dir": settings.base_dir, "time": time.time()}


# 获取文件列表
@app.get("/api/files")
async def get_files(path: str = ""):
    files = await file_manager.get_file_list(path)
    return {"files": files, "current_path": path}


# 创建文件夹
@app.post("/api/folders")
async def create_folder(
        request: Request,
        path: Optional[str] = Form(None),
        name: Optional[str] = Form(None)
):
    # 获取表单数据
    form_data = await request.form()

    # 从表单数据中获取参数
    path = form_data.get('path', '')
    name = form_data.get('name', '')

    if not name:
        return {"success": False, "error": "Folder name is required"}

    print(f"Creating folder: path={path}, name={name}")
    success = await file_manager.create_folder(path, name)
    return {"success": success}


# 批量删除
@app.delete("/api/items")
async def delete_items(paths: str = Form(...)):
    # 解析paths
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
async def init_upload(
        request: Request
):
    """使用 Request 对象直接获取表单数据"""
    print("=== Upload Init Request ===")

    try:
        form_data = await request.form()

        # 手动提取字段
        file_id = form_data.get('file_id')
        file_name = form_data.get('file_name')
        file_size = form_data.get('file_size')
        target_path = form_data.get('target_path', '')
        total_chunks = form_data.get('total_chunks')

        print(f"Extracted data: file_id={file_id}, file_name={file_name}, file_size={file_size}, target_path='{target_path}', total_chunks={total_chunks}")

        # 验证必要字段
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

        # 转换类型
        try:
            file_size_int = int(file_size)
            total_chunks_int = int(total_chunks)
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid number format: {e}"}
            )

        # 调用上传管理器
        result = await upload_manager.init_upload(
            file_id,
            file_name,
            file_size_int,
            target_path,
            total_chunks_int
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
    # 如果file_path是绝对路径，直接使用
    if os.path.isabs(file_path):
        full_path = file_path
    else:
        full_path = os.path.join(settings.base_dir, file_path)

    # 规范化路径
    full_path = os.path.normpath(full_path)

    # 安全检查
    if os.path.isabs(file_path) and not file_path.startswith(settings.base_dir):
        # 允许访问其他盘符
        pass
    else:
        # 如果在基础目录下，检查路径遍历
        try:
            common_path = os.path.commonpath([full_path, settings.base_dir])
            if common_path != settings.base_dir:
                raise HTTPException(status_code=403, detail="Access denied")
        except ValueError:
            raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(full_path) or os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    filename = os.path.basename(full_path)

    if preview:
        # 预览模式
        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type and mime_type.startswith(('image/', 'video/', 'audio/', 'text/', 'application/pdf')):
            return FileResponse(full_path, media_type=mime_type)

    # 下载模式
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
                # 检查客户端是否断开连接
                if await request.is_disconnected():
                    print("Client disconnected from SSE")
                    break

                try:
                    info = await file_manager.get_storage_info()
                    yield f"data: {json.dumps(info)}\n\n"
                    await asyncio.sleep(5)  # 每5秒推送一次
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"SSE Error: {e}")
                    break
        finally:
            print("SSE connection closed")

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
    """
    搜索文件
    - query: 搜索关键词
    - path: 搜索的起始路径（可选）
    """
    if not query or len(query.strip()) < 1:
        return {"files": [], "query": query, "path": path}

    results = await file_manager.search_files(query, path)
    return {"files": results, "query": query, "path": path}


# 移动/重命名接口
@app.post("/api/items/move")
async def move_items(request: Request):
    """
    移动或重命名项目
    支持两种模式：
    1. 重命名：提供 source 和 target（新名称）
    2. 移动到文件夹：提供 sources 和 destination
    """
    try:
        data = await request.json()

        # 模式1: 重命名单个文件
        if 'source' in data and 'target' in data:
            result = await file_manager.move_items(
                [{"source": data['source'], "target": data['target']}],
                ""
            )
            return result

        # 模式2: 批量移动到文件夹
        elif 'sources' in data and 'destination' in data:
            items = [{"source": s} for s in data['sources']]
            result = await file_manager.move_items(items, data['destination'])
            return result

        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request format. Expected {'source': path, 'target': name} or {'sources': [paths], 'destination': folder_path}"}
            )

    except Exception as e:
        print(f"Error in move_items: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# 重命名接口（单独）
@app.post("/api/items/rename")
async def rename_item(path: str = Form(...), new_name: str = Form(...)):
    """重命名文件或文件夹"""
    result = await file_manager.rename_item(path, new_name)
    return result


# 获取文件夹树（用于移动对话框）
@app.get("/api/folder-tree")
async def get_folder_tree(path: str = ""):
    """
    获取文件夹树结构
    """
    try:
        files = await file_manager.get_file_list(path)

        # 递归构建树
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
        print(f"Error building folder tree: {e}")
        return {"tree": []}


# 添加文件夹下载接口
@app.post("/api/download/folder")
async def download_folder(request: Request):
    """
    下载整个文件夹（打包为ZIP）
    """
    try:
        data = await request.json()
        folder_path = data.get('path')

        if not folder_path:
            raise HTTPException(status_code=400, detail="Folder path is required")

        # 获取完整路径
        if os.path.isabs(folder_path):
            full_path = folder_path
        else:
            full_path = os.path.join(settings.base_dir, folder_path)

        full_path = os.path.normpath(full_path)

        # 安全检查
        if os.path.isabs(folder_path) and not folder_path.startswith(settings.base_dir):
            pass
        else:
            try:
                common_path = os.path.commonpath([full_path, settings.base_dir])
                if common_path != settings.base_dir:
                    raise HTTPException(status_code=403, detail="Access denied")
            except ValueError:
                raise HTTPException(status_code=403, detail="Access denied")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Folder not found")

        if not os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail="Path is not a directory")

        # 创建临时ZIP文件
        folder_name = os.path.basename(full_path)
        if not folder_name:
            folder_name = "download"

        # 使用临时文件
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()

        try:
            # 创建ZIP文件
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 遍历文件夹
                for root, dirs, files in os.walk(full_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对路径
                        rel_path = os.path.relpath(file_path, os.path.dirname(full_path))
                        # 添加到ZIP
                        zipf.write(file_path, rel_path)

            # 返回ZIP文件
            return FileResponse(
                temp_zip.name,
                media_type='application/zip',
                filename=f"{folder_name}.zip",
                headers={
                    "Content-Disposition": f"attachment; filename={folder_name}.zip"
                }
            )
        except Exception as e:
            # 清理临时文件
            if os.path.exists(temp_zip.name):
                os.unlink(temp_zip.name)
            raise HTTPException(status_code=500, detail=f"Failed to create zip: {str(e)}")

    except Exception as e:
        print(f"Download folder error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download/batch")
async def download_batch(request: Request):
    """
    批量下载多个文件/文件夹（打包为ZIP）
    """
    try:
        data = await request.json()
        paths = data.get('paths', [])

        if not paths:
            raise HTTPException(status_code=400, detail="No paths provided")

        # 创建临时ZIP文件
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip.close()

        try:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for rel_path in paths:
                    # 获取完整路径
                    if os.path.isabs(rel_path):
                        full_path = rel_path
                    else:
                        full_path = os.path.join(settings.base_dir, rel_path)

                    full_path = os.path.normpath(full_path)

                    if not os.path.exists(full_path):
                        continue

                    if os.path.isdir(full_path):
                        # 添加文件夹
                        for root, dirs, files in os.walk(full_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                # 计算相对于基础目录的路径
                                rel_file_path = os.path.relpath(file_path, settings.base_dir)
                                zipf.write(file_path, rel_file_path)
                    else:
                        # 添加文件
                        rel_file_path = os.path.relpath(full_path, settings.base_dir)
                        zipf.write(full_path, rel_file_path)

            return FileResponse(
                temp_zip.name,
                media_type='application/zip',
                filename="download.zip"
            )
        except Exception as e:
            if os.path.exists(temp_zip.name):
                os.unlink(temp_zip.name)
            raise HTTPException(status_code=500, detail=f"Failed to create zip: {str(e)}")

    except Exception as e:
        print(f"Batch download error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 添加管理页面路由
@app.get("/docliu", response_class=HTMLResponse)
async def admin_page():
    import os
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
    admin_path = os.path.join(frontend_path, "admin.html")
    try:
        with open(admin_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return HTMLResponse(content=content)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>")

# 挂载前端静态文件
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


def get_local_ip():
    """获取本机IP地址"""
    try:
        # 创建一个UDP套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接到一个外部地址（不需要实际连接）
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def print_startup_info():
    """打印启动信息"""
    local_ip = get_local_ip()

    print("\n" + "=" * 60)
    print("🚀 文件共享系统启动成功！")
    print("=" * 60)
    print("\n📁 存储路径:", settings.base_dir)
    print("\n🌐 访问地址:")
    print(f"   📍 本地访问: http://localhost:8000")
    print(f"   📍 本机IP:   http://{local_ip}:8000")
    print(f"   📍 管理页面: http://localhost:8000/admin")
    print("\n📊 存储信息:")

    # 获取存储信息
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    storage_info = loop.run_until_complete(file_manager.get_storage_info())
    loop.close()

    print(f"   已用空间: {storage_info['used_gb']:.2f} GB")
    print(f"   剩余空间: {storage_info['free_gb']:.2f} GB")
    print(f"   总计空间: {storage_info['total_gb']} GB")
    print(f"   使用率: {storage_info['percentage']:.1f}%")
    print("\n📝 使用说明:")
    print("   - 按 Ctrl+C 停止服务")
    print("   - 配置文件: backend/config.json")
    print("   - 管理页面: http://localhost:8000/admin")
    print("=" * 60 + "\n")


# 添加启动脚本
def start_server():
    """启动服务器"""
    print_startup_info()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    start_server()