// src/api/index.js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://192.168.1.5:8000/api',
  timeout: 30000
})

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token')
    // console.log('[API] 请求URL:', config.url)
    // console.log('[API] 读取token:', token)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      // console.log('[API] 添加token到请求头')
    } else {
      // console.log('[API] 没有token，不添加到请求头')
    }
    return config
  },
  error => Promise.reject(error)
)

// src/api/index.js - 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    // console.log('[API] 响应错误:', error.response?.status, error.response?.data)

    if (error.response?.status === 401) {
      // console.log('[API] 收到 401 未授权，清除 token')
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_info')

      // 如果当前在管理后台且不是登录页，跳转到登录页
      if (window.location.pathname.startsWith('/admin') &&
          window.location.pathname !== '/admin/login') {
        // console.log('[API] 跳转到登录页')
        window.location.href = '/admin/login'
      }
    }
    return Promise.reject(error)
  }
)

// ==================== 文件管理 API ====================
export const fileApi = {
  // 获取文件列表
  getFiles: (path = '') => api.get('/files', { params: { path } }),

  // 创建文件夹 - 发送表单数据
  createFolder: (path, name) => {
    const formData = new FormData()
    formData.append('path', path)
    formData.append('name', name)
    return api.post('/folders', formData)
  },

  // 删除项目 - 发送表单数据
  deleteItems: (paths) => {
    // 确保 paths 是数组
    const pathsArray = Array.isArray(paths) ? paths : [paths]
    // 发送表单数据
    const formData = new FormData()
    formData.append('paths', JSON.stringify(pathsArray))
    return api.delete('/items', {
      data: formData
    })
  },

  // 重命名
  rename: (path, newName) => api.post('/items/rename', { path, new_name: newName }),

  // 移动项目
  moveItems: (sources, destination) => api.post('/items/move', { 
    sources: Array.isArray(sources) ? sources : [sources], 
    destination 
  }),

  // 搜索
  search: (query, path = '') => api.get('/search', { params: { query, path } }),

  // 获取文件夹树
  getFolderTree: (path = '') => api.get('/folder-tree', { params: { path } }),

  // 下载文件
  download: (filePath) => `/api/files/${encodeURIComponent(filePath)}`,

  // 预览文件
  preview: (filePath) => `/api/files/${encodeURIComponent(filePath)}?preview=true`,

  // 下载文件夹
  downloadFolder: (path) => api.post('/download/folder', { path }, { responseType: 'blob' }),

  // 批量下载
  batchDownload: (paths) => api.post('/download/batch', { paths }, { responseType: 'blob' })
}

// ==================== 上传管理 API ====================
export const uploadApi = {
  // 初始化上传 - 发送表单数据
  initUpload: (fileId, fileName, fileSize, targetPath, totalChunks) => {
    const formData = new FormData()
    formData.append('file_id', fileId)
    formData.append('file_name', fileName)
    formData.append('file_size', fileSize)
    formData.append('target_path', targetPath)
    formData.append('total_chunks', totalChunks)
    return api.post('/upload/init', formData)
  },

  // 上传分片
  uploadChunk: (fileId, chunkIndex, chunkData) => {
    const formData = new FormData()
    formData.append('file_id', fileId)
    formData.append('chunk_index', chunkIndex)
    formData.append('chunk_data', chunkData)
    return api.post('/upload/chunk', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 获取上传状态
  getUploadStatus: (fileId) => api.get(`/upload/status/${fileId}`),

  // 取消上传
  cancelUpload: (fileId) => api.delete(`/upload/${fileId}`)
}

// ==================== 存储管理 API ====================
export const storageApi = {
  // 获取存储信息
  getStorageInfo: () => api.get('/storage'),

  // 更新存储路径 - 发送表单数据
  updateStoragePath: (newPath) => {
    const formData = new FormData()
    formData.append('new_path', newPath)
    return api.post('/storage/path', formData)
  },

  // SSE 流
  getStorageStream: () => '/api/storage/stream'
}

// ==================== 系统 API ====================
export const systemApi = {
  // 健康检查
  healthCheck: () => api.get('/health'),

  // 操作日志
  getLogs: (params) => api.get('/admin/logs', { params }),

  // 获取统计数据
  getStats: () => api.get('/admin/stats'),

  // 获取监控流 URL
  getMonitorStream: () => '/api/admin/monitor/stream'
}

// ==================== 管理员 API ====================
export const adminApi = {
  login: (username, password) => api.post('/admin/login', { username, password }),
  logout: () => api.post('/admin/logout')
}

export default api