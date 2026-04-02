// src/api/index.js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://192.168.1.13:8000/api',
  timeout: 30000
})

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_info')
      if (window.location.pathname.startsWith('/admin') &&
          window.location.pathname !== '/admin/login') {
        window.location.href = '/admin/login'
      }
    }
    return Promise.reject(error)
  }
)

// ==================== 文件管理 API ====================
export const fileApi = {
  getFiles: (path = '') => api.get('/files', { params: { path } }),
  createFolder: (path, name) => {
    const formData = new FormData()
    formData.append('path', path)
    formData.append('name', name)
    return api.post('/folders', formData)
  },
  deleteItems: (paths) => {
    const pathsArray = Array.isArray(paths) ? paths : [paths]
    const formData = new FormData()
    formData.append('paths', JSON.stringify(pathsArray))
    return api.delete('/items', { data: formData })
  },
  rename: (path, newName) => api.post('/items/rename', { path, new_name: newName }),
  moveItems: (sources, destination) => api.post('/items/move', {
    sources: Array.isArray(sources) ? sources : [sources],
    destination
  }),
  search: (query, path = '') => api.get('/search', { params: { query, path } }),
  getFolderTree: (path = '') => api.get('/folder-tree', { params: { path } }),
  preview(path) {
    const encodedPath = encodeURIComponent(path).replace(/%2F/g, '/')
    return `/api/files/${encodedPath}?preview=true`
  },
  download(path) {
    const encodedPath = encodeURIComponent(path).replace(/%2F/g, '/')
    return `/api/files/${encodedPath}`
  },
  downloadFolder: (path) => api.post('/download/folder', { path }, { responseType: 'blob' }),
  batchDownload: (paths) => api.post('/download/batch', { paths }, { responseType: 'blob' })
}

// ==================== 上传管理 API ====================
export const uploadApi = {
  initUpload: (fileId, fileName, fileSize, targetPath, totalChunks) => {
    const formData = new FormData()
    formData.append('file_id', fileId)
    formData.append('file_name', fileName)
    formData.append('file_size', fileSize)
    formData.append('target_path', targetPath)
    formData.append('total_chunks', totalChunks)
    return api.post('/upload/init', formData)
  },
  uploadChunk: (fileId, chunkIndex, chunkData) => {
    const formData = new FormData()
    formData.append('file_id', fileId)
    formData.append('chunk_index', chunkIndex)
    formData.append('chunk_data', chunkData)
    return api.post('/upload/chunk', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getUploadStatus: (fileId) => api.get(`/upload/status/${fileId}`),
  cancelUpload: (fileId) => api.delete(`/upload/${fileId}`)
}

// ==================== 存储管理 API ====================
export const storageApi = {
  getStorageInfo: () => api.get('/storage'),
  updateStoragePath: (newPath) => {
    const formData = new FormData()
    formData.append('new_path', newPath)
    return api.post('/storage/path', formData)
  },
  getStorageStream: () => '/api/storage/stream'
}

// ==================== 系统 API ====================
export const systemApi = {
  healthCheck: () => api.get('/health'),
  getLogs: (params) => api.get('/admin/logs', { params }),
  getStats: () => api.get('/admin/stats'),
  getMonitorStream: () => '/api/admin/monitor/stream'
}

// ==================== 管理员 API ====================
export const adminApi = {
  login: (username, password) => api.post('/admin/login', { username, password }),
  logout: () => api.post('/admin/logout')
}

export default api