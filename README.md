# AuroraShare · 极光共享 - 现代化文件共享系统

<div align="center">

🚀 **让文件共享像极光一样绚丽流畅！**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [使用指南](#-使用指南) • [配置说明](#-配置说明) • [API 文档](#-api-接口) • [常见问题](#-常见问题) • [技术架构](#-技术架构)

</div>

---

## 📋 项目简介

AuroraShare · 极光共享是一个基于 FastAPI 的现代化文件共享系统，采用前后端分离架构，提供**断点续传**、**文件夹上传**、**文件预览**等核心功能。系统设计注重性能与用户体验，支持跨平台部署，让文件共享变得前所未有的简单高效。

### ✨ 核心亮点

- ⚡ **极速上传** - 8MB 分片并发上传，充分利用带宽
- 🔄 **断点续传** - 意外中断？继续上传只需一秒
- 🖱️ **拖拽上传** - 从桌面直接拖拽文件到网页即可上传，带视觉反馈
- 📁 **整文件夹上传** - 保持原有目录结构完整上传
- 👁️ **多格式预览** - 图片、视频、音频、PDF、文本在线预览
- 💾 **空间监控** - 实时磁盘使用情况可视化（SSE 推送）
- 🎨 **美观界面** - 现代化设计，支持亮/暗主题切换
- 🔍 **智能搜索** - 实时搜索，高亮显示匹配结果

---

## ✨ 功能特性

### 📁 文件管理

#### 基础操作
- ✅ **文件夹管理** - 创建、删除、重命名文件夹
- ✅ **文件操作** - 上传、下载、删除、重命名文件
- ✅ **批量处理** - 多选批量删除、批量下载（打包 ZIP）
- ✅ **移动/复制** - 拖拽移动文件到目标文件夹

#### 高级功能
- 🔍 **智能搜索** - 关键词实时搜索，高亮显示匹配结果
- 📂 **文件夹树** - 清晰的层级结构，快速定位目录
- 🏷️ **面包屑导航** - 直观显示当前路径，点击快速跳转
- ↩️ **返回上级** - Backspace 快捷键快速返回上一级

### 📤 上传特性

#### 核心能力
- ⚡ **断点续传** - 8MB 分片上传，中断后可继续
- 📁 **文件夹上传** - 保持原有目录结构完整上传
- 🖱️ **拖拽上传** - 从桌面直接拖拽文件到网页即可上传，带蓝色边框视觉反馈
- 🚀 **并发上传** - 最多 6 个分片同时上传，速度提升 3 倍

#### 用户体验
- 📊 **实时进度** - 精确显示每个文件的上传进度
- 🎯 **上传队列** - 可视化管理多个上传任务
- ⏸️ **暂停/继续** - 随时控制上传任务
- ❌ **取消上传** - 支持取消正在进行的上传
- 💫 **弹出动画** - 拖拽时平滑的 scale 动画效果
- 🌗 **暗色模式** - 完美支持深色主题

### 👁️ 文件预览

#### 支持的格式
- 🖼️ **图片** - JPG, PNG, GIF, WebP, SVG, BMP
- 🎬 **视频** - MP4, WebM, AVI, MOV
- 🎵 **音频** - MP3, WAV, OGG, FLAC
- 📄 **文档** - PDF, TXT, MD, DOCX
- 💻 **代码** - 支持语法高亮的代码文件

### 💾 存储管理

#### 空间监控
- 📊 **使用统计** - 已用空间、剩余空间、使用率百分比
- 📈 **实时推送** - SSE 技术每 5 秒更新，无需刷新页面
- 🔧 **路径配置** - 支持自定义存储位置（可跨盘符）
- 🧹 **自动清理** - 24 小时自动清理未完成的临时文件
- 📦 **智能管理** - 临时文件存储在 `.temp_uploads` 目录，不显示在界面

### 🛡️ 系统安全

- 🔒 **路径防护** - 防止目录穿越攻击
- ✅ **权限验证** - 写入权限测试
- 🚫 **类型限制** - 可配置允许的文件类型
- 🕵️ **隐藏文件** - 自动过滤系统和临时文件

---

## 🏗️ 技术架构

### 后端技术栈

| 技术 | 说明 |
|------|------|
| **FastAPI** | 高性能异步 Web 框架 |
| **Uvicorn** | ASGI 服务器 |
| **aiofiles** | 异步文件 I/O |
| **asyncio** | 异步并发处理 |
| **ThreadPoolExecutor** | 线程池并发 |

### 前端技术栈

| 技术 | 说明 |
|------|------|
| **Vue.js 2.x** | 渐进式 JavaScript 框架 |
| **Element UI** | Vue.js 组件库 |
| **HTML5** | 语义化标签、拖拽 API |
| **CSS3** | Flexbox、Grid、自定义变量、Backdrop-filter |
| **JavaScript ES6+** | 现代 JavaScript 特性 |
| **Font Awesome 6** | 图标库 |
| **Fetch API** | HTTP 请求 |
| **SSE** | 服务器推送（EventSource） |
| **CSS3 Animations** | transform、scale 动画 |

---

## 📁 项目结构

```
file-share/
├── backend/                # 后端代码
│   ├── main.py            # 主应用入口 & API 接口
│   ├── config.py          # 配置管理（端口、路径、日志）
│   ├── file_manager.py    # 文件管理核心
│   ├── upload_manager.py  # 上传管理（断点续传）
│   ├── logger.py          # 日志管理
│   ├── requirements.txt   # 依赖列表
│   └── config.json        # 配置文件（自动生成）
│
├── frontend/               # 前端代码
│   ├── index.html         # 主页面（文件管理 + 拖拽上传）
│   └── admin.html         # 管理页面（存储配置）
│
├── image/                  # 项目截图
│   ├── img_1.png
│   ├── img_2.png
│   ├── img_3.png
│   ├── img_4.png
│   ├── img_5.png
│   └── img_6.png
├── run.py                  # 启动脚本（支持动态端口 + 自动打开浏览器）
├── build_Windows.bat       # Windows 打包脚本
├── build_Windows.py        # Windows 打包配置
├── icon.ico                # 应用图标
├── LICENSE                 # 许可证
└── README.md              # 项目文档
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.8+
- **浏览器**: Chrome、Firefox、Edge 等现代浏览器

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/liu17y/file_share.git
git clone https://gitee.com/Liuzongyi-liu/file-share.git
cd file-share
```

#### 2. 安装依赖

```bash
pip install -r backend/requirements.txt
```

**依赖说明：**
- `fastapi` - 高性能 Web 框架
- `uvicorn` - ASGI 服务器
- `aiofiles` - 异步文件 I/O
- `python-multipart` - 表单数据处理
- `jinja2` - 模板引擎
- `watchdog` - 文件监控
- `psutil` - 系统信息

#### 3. 启动服务

**方法一：使用启动脚本（推荐）**
```bash
python run.py
```
✨ **优势：** 自动打开浏览器、动态端口检测、完整日志记录

**方法二：直接启动**
```bash
cd backend
python main.py
```

**方法三：使用配置文件**
编辑 `backend/config.json` 配置端口和存储路径后启动。

#### 4. 访问应用

- **主页面**: http://localhost:8000
- **管理页面**: http://localhost:8000/docliu
- **API 文档**: http://localhost:8000/docs（FastAPI 自动生成）

**提示：** 如果 8000 端口被占用，系统会自动选择 8001-8010 范围内的可用端口。

---

## 📖 使用指南

### 文件管理

#### 浏览文件
- 点击文件夹进入下一级
- 使用面包屑导航返回上级目录
- 按 `Backspace` 键快速返回上一级

#### 上传文件
1. **点击按钮上传**
   - 点击"上传文件"按钮
   - 选择一个或多个文件
   - 在上传对话框中查看进度

2. **拖拽上传**
   - 从桌面或文件管理器选中文件
   - 拖拽到网页文件列表区域
   - 松开鼠标自动开始上传

#### 上传文件夹
1. 点击"上传文件夹"按钮
2. 选择要上传的整个文件夹
3. 系统自动保持目录结构上传

#### 拖拽上传（v1.2.1 新增）
1. **从桌面或文件管理器选中文件**
2. **拖拽到网页文件列表区域**
3. **看到蓝色虚线边框和中央提示层**
4. **松开鼠标，文件自动开始上传**

**视觉反馈：**
- 🔵 **蓝色虚线边框** - 拖拽经过时显示
- 💫 **中央覆盖层** - "松开鼠标上传文件"提示
- 🎨 **弹出动画** - 平滑的 scale 动画效果
- 🌓 **暗色模式** - 完美适配深色主题

**注意：** 内部拖拽（应用内文件移动）不会触发上传提示。

#### 新建文件夹
1. 点击"新建文件夹"按钮
2. 输入文件夹名称
3. 回车或点击创建

#### 删除文件/文件夹
1. 勾选要删除的项目
2. 点击"批量删除"按钮
3. 确认删除操作

#### 重命名
1. 点击文件右侧的"编辑"图标 ✏️
2. 输入新名称
3. 回车或点击确定

#### 预览文件
- 点击文件右侧的"预览"图标 👁️
- 支持的文件类型会在线打开

#### 下载文件
- 单个下载：点击下载图标 ⬇️
- 批量下载：选中多个文件后右键菜单选择

### 搜索功能

1. 在顶部搜索框输入关键词
2. 系统自动实时搜索（无需回车）
3. 匹配的文件和文件夹高亮显示
4. 点击搜索结果快速定位

### 存储管理

#### 查看存储信息
- 侧边栏实时显示：
  - 已用空间
  - 剩余空间
  - 总空间
  - 使用率百分比

#### 修改存储路径
1. 访问管理页面 `/admin`
2. 输入新的绝对路径（如 `D:\shared_files`）
3. 点击"更新存储路径"
4. 系统自动测试写入权限

---

## ⚙️ 配置说明

### 配置文件 `backend/config.json`

```json
{
    "base_dir": "uploads",
    "port": 8000,
    "port_range_start": 8000,
    "port_range_end": 8010,
    "host": "0.0.0.0",
    "max_upload_size_mb": 1024,
    "auto_open_browser": true,
    "debug": false,
    "version": "1.0.0"
}
```

### 可配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `base_dir` | 文件存储根路径（支持相对/绝对路径） | `uploads`（开发模式）/ `data/uploads`（打包模式） |
| `port` | 服务器端口 | 8000 |
| `port_range_start` | 端口范围起始 | 8000 |
| `port_range_end` | 端口范围结束 | 8010 |
| `host` | 监听地址 | `0.0.0.0` |
| `max_upload_size_mb` | 最大上传文件大小（MB） | 1024 |
| `auto_open_browser` | 是否自动打开浏览器 | true |
| `debug` | 调试模式 | false |

**注意：** 系统支持智能端口检测，如果配置的端口被占用，会自动在指定范围内寻找可用端口。

### 自定义修改

#### 修改分块大小
在 `backend/config.py` 中：
```python
self.chunk_size = 8 * 1024 * 1024  # 修改此值（默认 8MB）
```

#### 修改并发分片数
在前端 `index.html` 的 Vue 实例中：
```javascript
maxConcurrentChunks: 6  // 修改最大并发数（推荐 4-8）
```

#### 修改端口范围
在 `backend/config.py` 的 Settings 类中：
```python
self.default_port = 8000
self.port_range_start = 8000
self.port_range_end = 8010
```

---

## 📡 API 接口文档

### 文件操作

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/files?path=` | 获取文件列表（支持分页） |
| `POST` | `/api/folders` | 创建文件夹 |
| `DELETE` | `/api/items` | 批量删除（JSON/Form 数据） |
| `GET` | `/api/files/{path}` | 下载/预览文件 |
| `POST` | `/api/items/rename` | 重命名文件/文件夹（支持 JSON/Form） |
| `POST` | `/api/items/move` | 移动文件（支持单个/批量） |

**注意：** 所有路径参数使用 URL 编码，确保特殊字符正确处理。

### 上传管理

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/upload/init` | 初始化上传 |
| `POST` | `/api/upload/chunk` | 上传分块 |
| `GET` | `/api/upload/status/{id}` | 获取上传状态 |
| `DELETE` | `/api/upload/{id}` | 取消上传 |

### 存储管理

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/storage` | 获取存储信息 |
| `GET` | `/api/storage/stream` | SSE 实时推送 |
| `POST` | `/api/storage/path` | 更新存储路径 |

### 系统接口

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/search?query=` | 搜索文件 |
| `GET` | `/api/folder-tree` | 获取文件夹树 |

### 下载接口

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/download/folder` | 下载整个文件夹（ZIP） |
| `POST` | `/api/download/batch` | 批量下载（ZIP） |

---

## 🎯 性能优化

### 后端优化
- ✅ **异步 I/O** - 所有文件操作使用 `async/await`
- ✅ **并发控制** - 上传队列限制并发数
- ✅ **分片传输** - 8MB 分块，减少内存占用
- ✅ **线程池** - CPU 密集型任务使用线程池
- ✅ **智能端口** - 自动检测并选择可用端口
- ✅ **配置缓存** - 配置文件自动保存和加载

### 前端优化
- ✅ **按需加载** - 文件列表分页显示
- ✅ **防抖搜索** - 避免频繁请求
- ✅ **SSE 推送** - 每 5 秒更新，减少服务器压力
- ✅ **本地缓存** - 静态资源浏览器缓存
- ✅ **CSS3 动画** - 使用 transform 而非 top/left，提升拖拽性能
- ✅ **Backdrop-filter** - 毛玻璃效果硬件加速

### 网络优化
- ✅ **并发上传** - 6 个分片同时上传，速度提升 3 倍
- ✅ **断点续传** - 只上传未完成的分片
- ✅ **进度反馈** - 实时更新上传进度
- ✅ **视觉反馈** - 拖拽时蓝色边框 + 覆盖层提示

---

## 🧪 测试建议

### 功能测试清单

#### 文件管理
- [ ] 创建文件夹
- [ ] 删除文件夹（包含内容）
- [ ] 重命名文件夹
- [ ] 上传单个文件
- [ ] 上传多个文件
- [ ] 上传文件夹
- [ ] 删除文件
- [ ] 重命名文件
- [ ] 移动文件
- [ ] 批量删除

#### 上传功能
- [ ] 小文件上传（< 1MB）
- [ ] 大文件上传（> 100MB）
- [ ] 断点续传（上传中途关闭页面）
- [ ] 拖拽上传（从桌面拖拽文件）
- [ ] 拖拽视觉反馈（蓝色边框 + 覆盖层）
- [ ] 拖拽动画效果（scale 动画）
- [ ] 暗色模式下的拖拽显示
- [ ] 取消上传
- [ ] 并发上传

#### 预览功能
- [ ] 图片预览
- [ ] 视频预览
- [ ] 音频预览
- [ ] PDF 预览
- [ ] 文本预览

#### 搜索功能
- [ ] 文件名搜索
- [ ] 文件夹名搜索
- [ ] 部分匹配搜索
- [ ] 清除搜索

#### 其他功能
- [ ] 返回上级目录
- [ ] 面包屑导航
- [ ] 存储空间显示
- [ ] 暗色模式切换

---

## ⚠️ 注意事项

### 路径权限
- 修改存储路径时确保有写入权限
- Windows 系统注意管理员权限
- Linux 系统注意用户权限

### 磁盘空间
- 上传大文件前检查磁盘剩余空间
- 临时文件会占用额外空间
- 定期清理未完成的上传

### 并发上传
- 默认最大并发数为 6
- 可根据网络状况调整
- 过多并发可能导致网络拥堵

### 临时文件
- 未完成的上传保存在 `.temp_uploads` 目录
- 24 小时后自动清理
- 该目录不会在界面显示
- 手动清理：可直接删除该目录下的所有文件

### 浏览器兼容
- ✅ **推荐浏览器** - Chrome、Edge（支持所有特性包括文件夹拖拽）
- ✅ **其他浏览器** - Firefox、Safari（支持文件拖拽，文件夹拖拽可能受限）
- ❌ **IE 浏览器** - 不支持 HTML5 拖拽 API
- ✅ **移动端** - 基本兼容，但拖拽功能在触摸设备上可能受限

---

## ❓ 常见问题

### Q1: 为什么拖拽文件没有反应？
**A:** 请检查以下几点：
1. 确保使用的是现代浏览器（Chrome、Edge、Firefox）
2. 确认拖拽的是外部文件（桌面或文件管理器），不是应用内的文件
3. 查看是否出现蓝色边框和中央提示层
4. 检查浏览器控制台是否有错误信息

### Q2: 上传大文件时页面卡顿怎么办？
**A:** 建议：
1. 调整分块大小（默认 8MB），可改为 4MB 或更小
2. 减少并发分片数（默认 6），改为 4 或更小
3. 检查网络连接是否稳定
4. 关闭其他占用带宽的应用

### Q3: 如何修改存储路径？
**A:** 有三种方法：
1. **管理页面**：访问 `/docliu`，输入新路径后点击更新
2. **配置文件**：编辑 `backend/config.json` 的 `base_dir` 字段
3. **环境变量**：设置 `AURORA_UPLOAD_DIR` 环境变量

### Q4: 端口被占用怎么办？
**A:** 系统会自动检测并选择可用端口：
- 优先使用配置的端口（默认 8000）
- 如果占用，自动在 8001-8010 范围内寻找
- 仍然冲突，则由系统分配任意可用端口
- 启动日志会显示实际使用的端口

### Q5: 断点续传是如何工作的？
**A:** 工作原理：
1. 文件分片（默认 8MB/片）
2. 每片独立上传并标记为完成
3. 中断后重新上传时，只上传未完成的分片
4. 所有分片完成后合并为完整文件
5. 临时文件保存在 `.temp_uploads` 目录

### Q6: 支持哪些文件类型？
**A:** 理论上支持所有文件类型，预览功能支持：
- 🖼️ **图片**：JPG, PNG, GIF, WebP, SVG, BMP
- 🎬 **视频**：MP4, WebM, AVI, MOV
- 🎵 **音频**：MP3, WAV, OGG, FLAC
- 📄 **文档**：PDF, TXT, MD, DOCX
- 💻 **代码**：各种编程语言源文件

### Q7: 如何清理临时文件？
**A:** 有两种方法：
1. **自动清理**：系统会在 24 小时后自动清理
2. **手动清理**：直接删除 `.temp_uploads` 目录下的所有文件

### Q8: 可以在局域网中访问吗？
**A:** 可以！系统默认监听 `0.0.0.0`，局域网内其他设备可通过：
```
http://你的 IP 地址：端口号
```
访问。例如：`http://192.168.1.100:8000`

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 贡献步骤

1. **Fork 本项目** - 点击右上角 Fork 按钮
2. **克隆到本地** - `git clone git@github.com:你的用户名/file_share.git`
3. **创建特性分支** - `git checkout -b feature/AmazingFeature`
4. **提交更改** - `git commit -m 'Add some AmazingFeature'`
5. **推送到分支** - `git push origin feature/AmazingFeature`
6. **提交 Pull Request** - 在 GitHub/Gitee 上创建 PR

### 代码规范

- 遵循 PEP 8 风格指南（Python）
- 使用有意义的变量和函数名
- 添加必要的注释和文档字符串
- 确保代码通过现有测试

### 报告问题

提交 Issue 时请包含：
- 系统环境（操作系统、浏览器版本）
- 问题描述（清晰说明发生了什么问题）
- 重现步骤（如何触发这个问题）
- 期望行为（应该发生什么）
- 截图或日志（如果适用）

### 功能建议

我们欢迎新功能建议！请提供：
- 功能描述和应用场景
- 为什么这个功能有价值
- 可能的实现思路（可选）

### 开发环境搭建

```bash
# 克隆项目
git clone https://github.com/liu17y/file_share.git
cd file-share

# 安装依赖
pip install -r backend/requirements.txt

# 启动开发服务器
python run.py
```

---

## 📝 版本历史

### v1.2.1 (2026-03-20) - 拖拽上传视觉增强版

✨ **重大更新**
- 🎨 **拖拽上传视觉增强** - 蓝色虚线边框高亮 + 中央覆盖层提示
- 💫 **美观的弹出动画** - 平滑的 scale 动画效果
- 🌗 **暗色模式适配** - 完美支持深色主题
- 📱 **智能边界检测** - 精确识别拖拽区域
- ⚡ **性能优化** - 使用 CSS3 transform 和 backdrop-filter

🎯 **用户体验提升**
- ✅ 清晰的视觉反馈：拖拽时显示蓝色边框
- ✅ 友好的提示文字："松开鼠标上传文件"
- ✅ 侧边栏高亮标识：明确告知用户支持拖拽
- ✅ 多文件支持：同时检测多个拖拽文件

🐛 **问题修复**
- 优化拖拽事件处理逻辑
- 修复搜索模式下的拖拽冲突
- 改进内部拖拽与外部上传的区分

### v1.2.0 (2026-03-20)
✨ **新增功能**
- 文件/文件夹重命名功能
- 拖拽上传功能（外部文件）
- 返回上级目录功能
- Backspace 快捷键支持
- 隐藏临时目录显示

🐛 **问题修复**
- 修复分片上传文件损坏问题
- 优化并发上传逻辑
- 改进文件大小计算

### v1.1.0 (2024-02-01)
- ✨ 添加文件夹上传支持
- ✨ 优化上传队列显示
- ✨ 添加管理页面
- ✨ 支持文件预览

### v1.0.0 (2024-01-15)
- 🎉 初始版本发布
- ✅ 支持基础文件管理
- ✅ 实现断点续传功能
- ✅ 基本的 UI 界面

---

## 📄 许可证

本项目采用 **MIT 许可证**

详见 [LICENSE](LICENSE) 文件。

### 第三方库

- **Font Awesome** - 图标库
- **Element UI** - Vue.js 组件库
- **FastAPI** - Web 框架
- **aiofiles** - 异步文件操作

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者！

### 特别感谢

- **FastAPI 团队** - 提供的高性能异步 Web 框架
- **Element UI 团队** - 提供的 Vue.js 组件库
- **Font Awesome** - 提供的精美图标库
- **Vue.js 团队** - 提供的渐进式 JavaScript 框架
- **Uvicorn 团队** - 提供的 ASGI 服务器

### 使用的开源项目

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [Vue.js](https://vuejs.org/) - The Progressive JavaScript Framework
- [Element UI](https://element.eleme.io/) - A Desktop Component Library
- [Font Awesome](https://fontawesome.com/) - The Internet's Icon Library
- [Uvicorn](https://www.uvicorn.org/) - An ASGI web server
- [aiofiles](https://github.com/Tinche/aiofiles) - File support for asyncio

---

---

## 📞 联系方式

- **Gitee 仓库**: https://gitee.com/Liuzongyi-liu/file-share.git
- **GitHub 仓库**: https://github.com/liu17y/file_share.git
- **问题反馈**: 通过 Gitee/GitHub Issues 提交
- **邮箱**: your.email@example.com

---

<div align="center">

**AuroraShare · 极光共享 - 让文件传输如极光般绚丽流畅！** 🚀

### 📸 界面预览

![主界面](https://gitee.com/Liuzongyi-liu/file-share/raw/master/image/img_1.png)


![拖拽上传](https://gitee.com/Liuzongyi-liu/file-share/raw/master/image/img_2.png)


![文件预览](https://gitee.com/Liuzongyi-liu/file-share/raw/master/image/img_3.png)

![暗色模式](https://gitee.com/Liuzongyi-liu/file-share/raw/master/image/img_4.png)

![管理页面](https://gitee.com/Liuzongyi-liu/file-share/raw/master/image/img_5.png)

![文件夹树](https://gitee.com/Liuzongyi-liu/file-share/raw/master/image/img_6.png)

</div>

## ? 待完成
前端
vue3 + Varlet + echarts
文件共享
1、客户端不需要登陆就能进行所有操作
2、后台管理需要登陆
  2.1 操作日志
- 2.2 监控
- 2.3分析
- 2.4磁盘存储信息
- 2.5存储位置修改
