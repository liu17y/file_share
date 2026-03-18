import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
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

# ... (app 初始化后)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 允许所有来源
    allow_credentials=True,       # 允许携带凭证（如 Cookies）
    allow_methods=["*"],          # 允许所有 HTTP 方法 (GET, POST, PUT, DELETE 等)
    allow_headers=["*"],          # 允许所有请求头
)

# 确保上传目录存在
os.makedirs(settings.base_dir, exist_ok=True)


# 启动事件 - 在应用启动时启动上传处理器
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
    # 解析paths，因为Form数据可能是JSON字符串
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


# 初始化上传（断点续传）- 使用更宽松的类型
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
    # 如果file_path是绝对路径（其他盘符），直接使用
    if os.path.isabs(file_path):
        full_path = file_path
    else:
        full_path = os.path.join(settings.base_dir, file_path)

    # 规范化路径
    full_path = os.path.normpath(full_path)

    # 安全检查：确保文件在允许的范围内
    # 如果是绝对路径且不在基础目录下，检查是否在允许的盘符
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


# 添加管理页面路由
@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    admin_path = os.path.join(frontend_path, "admin.html")
    if os.path.exists(admin_path):
        with open(admin_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Admin page not found</h1><p>Please create admin.html in frontend directory</p>")


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
        reload=False,  # 生产环境关闭热重载
        log_level="info"
    )


if __name__ == "__main__":
    start_server()