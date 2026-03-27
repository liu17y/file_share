# AuroraShare Web Frontend

## 📋 项目简介

AuroraShare · 极光共享的前端项目，基于 Vue 3 + Vite + Varlet UI 构建，提供现代化的文件管理界面。

## 🛠️ 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 快速的前端构建工具
- **Varlet UI** - 轻量级移动端优先的组件库
- **ECharts** - 数据可视化图表库
- **Vue Router** - 路由管理
- **Pinia** - 状态管理

## 🚀 快速开始

### 环境要求

- **Node.js**: 16.0+
- **npm**: 7.0+

### 安装步骤

```bash
# 安装依赖
npm install

# 开发模式启动
npm run dev

# 生产构建
npm run build
```

## 📁 项目结构

```
web/
├── public/              # 静态资源
├── src/
│   ├── assets/         # 图片、样式等资源
│   ├── components/     # 组件
│   │   ├── FileList.vue        # 文件列表组件
│   │   ├── UploadDialog.vue    # 上传对话框组件
│   │   └── StorageInfo.vue     # 存储信息组件
│   ├── views/          # 页面
│   │   ├── FileManager.vue     # 文件管理器主页面
│   │   └── admin/
│   │       ├── Logs.vue        # 操作日志页面
│   │       └── Stats.vue       # 统计分析页面
│   ├── api/            # API 接口
│   ├── router/         # 路由配置
│   ├── store/          # 状态管理
│   ├── utils/          # 工具函数
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── index.html          # HTML 模板
├── vite.config.js      # Vite 配置
├── package.json        # 项目配置
└── README.md           # 项目文档
```

## ✨ 核心功能

### 文件管理
- 📁 文件夹上传与管理
- 📤 文件上传（支持断点续传）
- 📥 文件下载（支持批量下载）
- 🔍 智能搜索
- 🎨 拖拽上传（带视觉反馈）

### 界面特性
- 🌗 支持亮/暗主题切换
- 📱 响应式设计，支持多端部署
- 🎯 顶部操作栏支持折叠/抽屉展示
- 💾 实时存储信息监控

### 管理功能
- 📋 操作日志查看
- 📊 系统统计分析
- 🔧 存储路径配置
- 🎯 系统监控

## 🔧 配置说明

### Vite 配置 (`vite.config.js`)

```javascript
export default defineConfig({
  base: './',  // 保持相对路径，支持多端部署
  build: {
    outDir: '../frontend_dist',
    emptyOutDir: true,
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'ui': ['@varlet/ui'],
          'charts': ['echarts']
        }
      }
    }
  }
})
```

## 🎨 界面预览

### 主界面
![主界面]()

### 拖拽上传
![拖拽上传]()

### 暗色模式
![暗色模式]()

### 管理页面
![管理页面]()

## 📝 版本历史

### v1.2.2 (2026-03-21) - 性能优化与功能修复版
- ⚡ **上传文件夹卡顿优化** - 实现文件树递归遍历的异步处理
- 🔧 **操作日志加载修复** - 读取根目录下 logs 文件夹的实际日志
- 🎨 **多端部署布局优化** - 顶部操作栏支持折叠/抽屉展示

### v1.2.1 (2026-03-20) - 拖拽上传视觉增强版
- 🎨 **拖拽上传视觉增强** - 蓝色虚线边框高亮 + 中央覆盖层提示
- 💫 **美观的弹出动画** - 平滑的 scale 动画效果
- 🌗 **暗色模式适配** - 完美支持深色主题

### v1.2.0 (2026-03-20)
- ✨ 文件/文件夹重命名功能
- ✨ 拖拽上传功能
- ✨ 返回上级目录功能

## 🤝 开发指南

### 代码规范
- 遵循 Vue 3 组合式 API 最佳实践
- 使用 ESLint 进行代码检查
- 组件命名使用 PascalCase
- 变量和函数命名使用 camelCase

### 开发建议
- 使用 `npm run dev` 启动开发服务器
- 开发时可使用 Vue DevTools 进行调试
- 构建前运行 `npm run lint` 检查代码质量

## 📄 许可证

本项目采用 **MIT 许可证**

## 📞 联系方式

- **Gitee 仓库**: https://gitee.com/Liuzongyi-liu/file-share.git
- **GitHub 仓库**: https://github.com/liu17y/file_share.git
