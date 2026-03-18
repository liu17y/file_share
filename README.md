嗖嗖传 (WhooshShare) - 文件共享系统
📋 项目简介
嗖嗖传是一个基于 FastAPI 的现代化文件共享系统，支持断点续传、文件夹上传、文件预览等核心功能。系统采用前后端分离架构，提供简洁美观的 Web 界面，让文件共享变得像"嗖"一下一样简单快速。

✨ 核心功能
1. 文件管理
📁 文件夹创建/删除

📄 文件上传/下载/删除

🔍 文件预览（图片、视频、音频、PDF、文本等）

📂 文件夹递归上传

🗑️ 批量删除

2. 上传特性
⚡ 断点续传（8MB 分块）

📊 上传队列管理

🔄 上传进度实时显示

📁 拖拽上传（支持文件和文件夹）

⏸️ 上传任务取消

3. 存储管理
💾 实时磁盘空间监控

📈 存储使用率可视化

🔧 可自定义存储路径（支持跨盘符）

📊 SSE 实时推送存储信息

4. 系统特性
🌐 跨平台支持（Windows/Linux/Mac）

🔌 RESTful API 接口

🎨 响应式界面设计

🔒 路径安全防护

📱 移动端适配

🏗️ 技术架构
后端技术栈
框架: FastAPI

服务器: Uvicorn

文件处理: aiofiles (异步文件操作)

并发处理: asyncio + ThreadPoolExecutor

配置管理: JSON 配置文件

前端技术栈
HTML5: 语义化标签

CSS3: 自定义变量、Flexbox、Grid

JavaScript: ES6+、异步编程

图标库: Font Awesome 6

通信: Fetch API + SSE

📁 项目结构
text
file-share-system/
├── backend/                # 后端代码
│   ├── main.py            # 主应用入口
│   ├── config.py          # 配置管理
│   ├── file_manager.py    # 文件管理核心
│   ├── upload_manager.py  # 上传管理（断点续传）
│   ├── requirements.txt   # 依赖列表
│   └── config.json        # 配置文件（自动生成）
│
├── frontend/               # 前端代码
│   ├── index.html         # 主页面
│   ├── admin.html         # 管理页面
│   ├── css/
│   │   └── style.css      # 样式文件
│   └── js/
│       └── app.js         # 前端逻辑
│
├── run.py                  # 启动脚本（可选）
└── README.md              # 项目文档
🚀 快速开始
环境要求
Python 3.8+

现代浏览器（Chrome、Firefox、Edge等）

安装步骤
克隆项目

bash
git clone https://github.com/yourusername/file-share-system.git
cd file-share-system
安装依赖

bash
pip install -r backend/requirements.txt
启动服务

bash
# 方法1：使用启动脚本
python run.py

# 方法2：直接启动
cd backend
python main.py
访问应用

主页面：http://localhost:8000

管理页面：http://localhost:8000/admin

📖 使用指南
文件管理
浏览文件：点击文件夹进入，面包屑导航返回

上传文件：点击"上传文件"按钮或拖拽到虚线区域

上传文件夹：点击"上传文件夹"选择整个文件夹

新建文件夹：点击"新建文件夹"输入名称

删除文件：勾选文件后点击"删除选中"，或点击单个文件的删除按钮

预览文件：点击文件旁的预览按钮（支持图片、视频、音频、PDF、文本）

下载文件：点击下载按钮直接下载

存储管理
查看存储信息：侧边栏实时显示存储空间使用情况

修改存储路径：

进入管理页面 /admin
输入新的绝对路径（如 D:\shared_files）
点击"更新存储路径"
断点续传
大文件自动分块上传（8MB/块）

上传过程中断后，重新上传会自动续传

上传队列显示每个文件的进度

⚙️ 配置说明
配置文件 backend/config.json
json
{
    "base_dir": "C:\\Users\\YourName\\FileShare"
}
可配置参数
base_dir: 文件存储根路径（支持跨盘符）

🔧 自定义修改
修改分块大小
在 config.py 中：

python
self.chunk_size = 8 * 1024 * 1024  # 修改此值（默认8MB）
修改允许的文件类型
在 config.py 中：

python
self.allowed_extensions = {'.txt', '.pdf', '.png', ...}  # 添加/删除类型
📡 API 接口文档
文件操作
方法	端点	说明
GET	/api/files?path=	获取文件列表
POST	/api/folders	创建文件夹
DELETE	/api/items	批量删除
GET	/api/files/{path}	下载/预览文件
上传管理
方法	端点	说明
POST	/api/upload/init	初始化上传
POST	/api/upload/chunk	上传分块
GET	/api/upload/status/{id}	获取上传状态
DELETE	/api/upload/{id}	取消上传
系统信息
方法	端点	说明
GET	/api/storage	获取存储信息
GET	/api/storage/stream	SSE 实时推送
POST	/api/storage/path	更新存储路径
GET	/api/health	健康检查
🎯 性能优化
异步处理：所有 I/O 操作均使用异步方式

并发控制：上传队列限制并发数，避免资源耗尽

分块传输：大文件分块上传，支持断点续传

缓存控制：静态文件使用浏览器缓存

实时推送：SSE 替代轮询，减少服务器压力

🤝 贡献指南
Fork 项目

创建特性分支 (git checkout -b feature/AmazingFeature)

提交更改 (git commit -m 'Add some AmazingFeature')

推送到分支 (git push origin feature/AmazingFeature)

提交 Pull Request

📝 版本历史
v1.0.0 (2024-01-15)

初始版本发布

支持基础文件管理

实现断点续传功能

v1.1.0 (2024-02-01)

添加文件夹上传支持

优化上传队列显示

添加管理页面

⚠️ 注意事项
路径权限：修改存储路径时确保有写入权限

磁盘空间：上传大文件时注意磁盘剩余空间

并发上传：默认最大并发数为 4，可根据需要调整

临时文件：未完成的上传会保存在 .temp_uploads 目录，24小时后自动清理

📄 许可证
MIT License

Font Awesome 图标库

所有贡献者

嗖嗖传 - 让文件传输像"嗖"一样快！🚀

