<script setup>
import { ref, onMounted, computed } from 'vue'
import * as echarts from 'echarts'

// 响应式数据
const currentPath = ref('')
const files = ref([])
const folders = ref([])
const isLoading = ref(false)
const uploadDialogVisible = ref(false)
const newFolderName = ref('')
const createFolderDialogVisible = ref(false)
const searchQuery = ref('')
const storageInfo = ref({})
const uploadProgress = ref(0)
const isUploading = ref(false)
const uploadQueue = ref([])

// 工具方法
const getFileIcon = (type) => {
  if (!type) return 'file'
  if (type.includes('image')) return 'image'
  if (type.includes('video')) return 'video-camera'
  if (type.includes('audio')) return 'headphones'
  if (type.includes('pdf')) return 'document'
  if (type.includes('text')) return 'file-text'
  return 'file'
}

const formatFileSize = (size) => {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

// 计算属性
const filteredFiles = computed(() => {
  if (!searchQuery.value) {
    return files.value
  }
  const query = searchQuery.value.toLowerCase()
  return files.value.filter(file => 
    !file.is_dir && file.name.toLowerCase().includes(query)
  )
})

// 加载文件列表
const loadFiles = async (path = '') => {
  isLoading.value = true
  try {
    const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`)
    const data = await response.json()
    files.value = data.files || []
    currentPath.value = data.current_path
    // 分离文件和文件夹
    folders.value = files.value.filter(item => item.is_dir)
  } catch (error) {
    console.error('加载文件失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 加载存储信息
const loadStorageInfo = async () => {
  try {
    const response = await fetch('/api/storage')
    storageInfo.value = await response.json()
  } catch (error) {
    console.error('加载存储信息失败:', error)
  }
}

// 创建文件夹
const createFolder = async () => {
  if (!newFolderName.value.trim()) return
  
  try {
    const formData = new FormData()
    formData.append('path', currentPath.value)
    formData.append('name', newFolderName.value)
    
    const response = await fetch('/api/folders', {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    if (data.success) {
      loadFiles(currentPath.value)
      createFolderDialogVisible.value = false
      newFolderName.value = ''
    }
  } catch (error) {
    console.error('创建文件夹失败:', error)
  }
}

// 删除文件/文件夹
const deleteItem = async (path) => {
  if (!confirm('确定要删除吗？')) return
  
  try {
    const formData = new FormData()
    formData.append('paths', JSON.stringify([path]))
    
    const response = await fetch('/api/items', {
      method: 'DELETE',
      body: formData
    })
    
    await response.json()
    loadFiles(currentPath.value)
  } catch (error) {
    console.error('删除失败:', error)
  }
}

// 重命名文件/文件夹
const renameItem = async (item, newName) => {
  try {
    const response = await fetch('/api/items/rename', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        path: item.path,
        new_name: newName
      })
    })
    
    const data = await response.json()
    if (data.success) {
      loadFiles(currentPath.value)
    }
  } catch (error) {
    console.error('重命名失败:', error)
  }
}

// 上传文件
const handleFileUpload = async (event) => {
  const files = event.target.files
  if (files.length === 0) return
  
  for (const file of files) {
    await uploadFile(file)
  }
}

// 上传单个文件
const uploadFile = async (file) => {
  const fileId = Date.now() + Math.random().toString(36).substr(2, 9)
  const chunkSize = 8 * 1024 * 1024 // 8MB
  const totalChunks = Math.ceil(file.size / chunkSize)
  
  // 初始化上传
  const initResponse = await fetch('/api/upload/init', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded'
    },
    body: new URLSearchParams({
      file_id: fileId,
      file_name: file.name,
      file_size: file.size.toString(),
      target_path: currentPath.value,
      total_chunks: totalChunks.toString()
    })
  })
  
  const initData = await initResponse.json()
  if (!initData.success) {
    return
  }
  
  // 上传分块
  let uploadedChunks = 0
  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize
    const end = Math.min(start + chunkSize, file.size)
    const chunk = file.slice(start, end)
    
    const formData = new FormData()
    formData.append('file_id', fileId)
    formData.append('chunk_index', i.toString())
    formData.append('chunk_data', chunk)
    
    const chunkResponse = await fetch('/api/upload/chunk', {
      method: 'POST',
      body: formData
    })
    
    const chunkData = await chunkResponse.json()
    if (chunkData.success) {
      uploadedChunks++
      uploadProgress.value = Math.round((uploadedChunks / totalChunks) * 100)
    } else {
      return
    }
  }
  
  // 上传完成后刷新文件列表
  uploadProgress.value = 0
  loadFiles(currentPath.value)
}

// 下载文件
const downloadFile = (file) => {
  window.open(`/api/files/${encodeURIComponent(file.path)}`, '_blank')
}

// 预览文件
const previewFile = (file) => {
  window.open(`/api/files/${encodeURIComponent(file.path)}?preview=true`, '_blank')
}

// 进入文件夹
const enterFolder = (folder) => {
  loadFiles(folder.path)
}

// 返回上级目录
const goBack = () => {
  const parentPath = currentPath.value.split('/').filter(Boolean).slice(0, -1).join('/')
  loadFiles(parentPath)
}

// 初始化 SSE 连接
const initSSE = () => {
  const eventSource = new EventSource('/api/storage/stream')
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      storageInfo.value = data
    } catch (error) {
      // 静默处理 SSE 数据解析错误
    }
  }
  
  eventSource.onerror = () => {
    eventSource.close()
  }
}

// 生命周期钩子
onMounted(() => {
  loadFiles()
  loadStorageInfo()
  initSSE()
})
</script>

<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="header-left">
        <h1>AuroraShare · 极光共享</h1>
      </div>
      <div class="header-right">
        <var-input
          v-model="searchQuery"
          placeholder="搜索文件..."
          class="search-input"
        >
          <template #prefix>
            <var-icon name="search" />
          </template>
        </var-input>
        <var-button @click="uploadDialogVisible = true" type="primary">
          <var-icon name="upload" />
          上传文件
        </var-button>
        <var-button @click="createFolderDialogVisible = true">
          <var-icon name="folder-add" />
          新建文件夹
        </var-button>
      </div>
    </div>
    
    <!-- 面包屑导航 -->
    <div class="breadcrumb">
      <var-button @click="loadFiles()" size="small" text>
        根目录
      </var-button>
      <var-divider direction="vertical" />
      <template v-if="currentPath">
        <template v-for="(segment, index) in currentPath.split('/').filter(Boolean)" :key="index">
          <var-button 
            @click="enterFolder({ path: currentPath.split('/').slice(0, index + 1).join('/') })" 
            size="small" 
            text
          >
            {{ segment }}
          </var-button>
          <var-divider v-if="index < currentPath.split('/').filter(Boolean).length - 1" direction="vertical" />
        </template>
      </template>
    </div>
    
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 侧边栏存储信息 -->
      <div class="sidebar">
        <div class="storage-info">
          <h3>存储信息</h3>
          <div class="storage-item">
            <span>总空间:</span>
            <span>{{ (storageInfo.total / (1024 * 1024 * 1024)).toFixed(2) }} GB</span>
          </div>
          <div class="storage-item">
            <span>已用空间:</span>
            <span>{{ (storageInfo.used / (1024 * 1024 * 1024)).toFixed(2) }} GB</span>
          </div>
          <div class="storage-item">
            <span>剩余空间:</span>
            <span>{{ (storageInfo.free / (1024 * 1024 * 1024)).toFixed(2) }} GB</span>
          </div>
          <div class="storage-item">
            <span>使用率:</span>
            <span>{{ storageInfo.percent }}%</span>
          </div>
          <div class="storage-chart">
            <div id="storageChart" style="width: 100%; height: 150px;"></div>
          </div>
        </div>
        
        <div class="nav-links">
          <var-button @click="$router.push('/admin')" size="large" block>
            <var-icon name="settings" />
            管理后台
          </var-button>
        </div>
      </div>
      
      <!-- 文件列表 -->
      <div class="file-list-container">
        <div class="file-list-header">
          <h2>文件列表</h2>
          <var-button v-if="currentPath" @click="goBack" size="small">
            <var-icon name="arrow-left" />
            返回上级
          </var-button>
        </div>
        
        <var-skeleton v-if="isLoading" :rows="5" />
        
        <div v-else class="file-list-scroll">
          <!-- 文件夹列表 -->
          <div v-for="folder in folders" :key="folder.path" class="file-item folder-item">
            <div class="file-icon">
              <var-icon name="folder" size="24" color="#409eff" />
            </div>
            <div class="file-info">
              <div class="file-name" @click="enterFolder(folder)">{{ folder.name }}</div>
              <div class="file-meta">文件夹</div>
            </div>
            <div class="file-actions">
              <var-button @click="deleteItem(folder.path)" size="small" type="danger" text>
                <var-icon name="delete" />
              </var-button>
              <var-button @click="renameItem(folder, prompt('请输入新名称:', folder.name))" size="small" text>
                <var-icon name="edit" />
              </var-button>
            </div>
          </div>
          
          <!-- 文件列表 -->
          <div v-for="file in filteredFiles" :key="file.path" class="file-item">
            <div class="file-icon">
              <var-icon 
                :name="getFileIcon(file.type)" 
                size="24" 
                color="#67c23a"
              />
            </div>
            <div class="file-info">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-meta">
                {{ file.type }}
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
              </div>
            </div>
            <div class="file-actions">
              <var-button @click="previewFile(file)" size="small" text>
                <var-icon name="eye" />
              </var-button>
              <var-button @click="downloadFile(file)" size="small" text>
                <var-icon name="download" />
              </var-button>
              <var-button @click="deleteItem(file.path)" size="small" type="danger" text>
                <var-icon name="delete" />
              </var-button>
              <var-button @click="renameItem(file, prompt('请输入新名称:', file.name))" size="small" text>
                <var-icon name="edit" />
              </var-button>
            </div>
          </div>
          
          <div v-if="filteredFiles.length === 0" class="empty-state">
            <var-icon name="folder-open" size="48" color="#c0c4cc" />
            <p>暂无文件</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 上传文件对话框 -->
    <var-dialog v-model:show="uploadDialogVisible" title="上传文件">
      <div class="upload-dialog-content">
        <input
          type="file"
          @change="handleFileUpload"
          accept="*/*"
          multiple
          class="file-input"
        />
        <div v-if="isUploading" class="upload-progress">
          <var-progress :percentage="uploadProgress" :show-text="true" />
        </div>
      </div>
      <template #footer>
        <var-button @click="uploadDialogVisible = false">取消</var-button>
      </template>
    </var-dialog>
    
    <!-- 新建文件夹对话框 -->
    <var-dialog v-model:show="createFolderDialogVisible" title="新建文件夹">
      <var-input v-model="newFolderName" placeholder="请输入文件夹名称" />
      <template #footer>
        <var-button @click="createFolderDialogVisible = false">取消</var-button>
        <var-button type="primary" @click="createFolder">创建</var-button>
      </template>
    </var-dialog>
  </div>
</template>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: 'Inter', 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

.header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 0 30px;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.header-left h1 {
  font-size: 24px;
  font-weight: 700;
  background: linear-gradient(135deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.search-input {
  width: 350px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.breadcrumb {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(5px);
  padding: 15px 30px;
  border-bottom: 1px solid rgba(200, 200, 200, 0.2);
  display: flex;
  align-items: center;
  gap: 15px;
}

.main-content {
  display: flex;
  padding: 30px;
  gap: 30px;
  min-height: calc(100vh - 140px);
}

.sidebar {
  width: 320px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 25px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.sidebar:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.storage-info h3 {
  margin-bottom: 20px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.storage-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-size: 14px;
  padding: 8px 12px;
  background: rgba(240, 242, 245, 0.8);
  border-radius: 8px;
  transition: background 0.3s ease;
}

.storage-item:hover {
  background: rgba(220, 230, 240, 0.8);
}

.storage-item span:first-child {
  color: #606266;
  font-weight: 500;
}

.storage-item span:last-child {
  color: #303133;
  font-weight: 600;
}

.storage-chart {
  margin-top: 25px;
  padding: 15px;
  background: rgba(240, 242, 245, 0.8);
  border-radius: 8px;
}

.nav-links {
  margin-top: 40px;
}

.file-list-container {
  flex: 1;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 30px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.file-list-container:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.file-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(200, 200, 200, 0.2);
}

.file-list-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-list-scroll {
  max-height: 600px;
  overflow-y: auto;
  padding-right: 10px;
}

.file-list {
  min-height: 400px;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(245, 247, 250, 0.5);
  border: 1px solid rgba(220, 230, 240, 0.3);
}

.file-item:hover {
  background: rgba(230, 240, 250, 0.8);
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.file-item.folder-item {
  background: rgba(235, 245, 230, 0.5);
  border: 1px solid rgba(200, 240, 200, 0.3);
}

.file-item.folder-item:hover {
  background: rgba(220, 240, 220, 0.8);
}

.file-icon {
  margin-right: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(64, 158, 255, 0.1);
  transition: all 0.3s ease;
}

.file-item:hover .file-icon {
  background: rgba(64, 158, 255, 0.2);
  transform: scale(1.1);
}

.file-item.folder-item .file-icon {
  background: rgba(103, 194, 58, 0.1);
}

.file-item.folder-item:hover .file-icon {
  background: rgba(103, 194, 58, 0.2);
}

.file-info {
  flex: 1;
}

.file-name {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #303133;
  transition: color 0.3s ease;
}

.file-item:hover .file-name {
  color: #409eff;
}

.file-meta {
  font-size: 14px;
  color: #909399;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-size {
  margin-left: 20px;
  background: rgba(200, 200, 200, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.file-actions {
  display: flex;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.3s ease, transform 0.3s ease;
  transform: translateY(5px);
}

.file-item:hover .file-actions {
  opacity: 1;
  transform: translateY(0);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  color: #909399;
  background: rgba(240, 242, 245, 0.5);
  border-radius: 12px;
  margin-top: 20px;
}

.empty-state p {
  margin-top: 15px;
  font-size: 16px;
  font-weight: 500;
}

.upload-dialog-content {
  padding: 30px 0;
}

.upload-progress {
  margin-top: 25px;
}

.file-input {
  display: block;
  width: 100%;
  padding: 15px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  background-color: rgba(245, 247, 250, 0.8);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  color: #909399;
}

.file-input:hover {
  border-color: #409eff;
  background-color: rgba(230, 240, 250, 0.8);
  color: #409eff;
}

.file-input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.2);
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(240, 242, 245, 0.5);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgba(150, 150, 150, 0.5);
  border-radius: 4px;
  transition: background 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 100, 100, 0.5);
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
    padding: 20px;
    gap: 20px;
  }
  
  .sidebar {
    width: 100%;
    padding: 20px;
  }
  
  .file-list-container {
    padding: 20px;
  }
  
  .header {
    padding: 0 20px;
  }
  
  .breadcrumb {
    padding: 10px 20px;
  }
  
  .search-input {
    width: 250px;
  }
}

/* 简化动画效果 */
.file-item {
  transition: all 0.2s ease;
}
</style>