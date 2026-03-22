<!-- src/views/client/FileManager.vue -->
<template>
  <div class="file-manager">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="logo">
        <var-icon name="flash" :size="28" color="#3f51b5" />
        <span>AuroraShare</span>
      </div>
      <div class="header-actions">
        <var-button class="custom-button custom-button--primary" @click="showUploadDialog = true">
          <var-icon name="upload" /> 上传文件
        </var-button>
        <var-button class="custom-button" @click="showFolderDialog = true">
          <var-icon name="folder-add" /> 新建文件夹
        </var-button>
        <var-button v-if="selectedItems.length" class="custom-button custom-button--danger" @click="handleBatchDelete">
          <var-icon name="delete" /> 删除 ({{ selectedItems.length }})
        </var-button>
        <var-button v-if="selectedItems.length" class="custom-button" @click="showMoveDialog = true">
          <var-icon name="folder-move" /> 移动
        </var-button>
        <var-button class="theme-toggle" @click="toggleDarkMode" :class="{ 'dark': isDarkMode }" round>
          <img v-if="!isDarkMode" src="/src/icons/sun.svg" alt="Sun" style="width: 20px; height: 20px; filter: invert(0%);" />
          <img v-else src="/src/icons/moon.svg" alt="Moon" style="width: 20px; height: 20px; filter: invert(100%);" />
        </var-button>
        <var-button class="custom-button custom-button--text" @click="goToAdmin">
          <var-icon name="settings" /> 管理
        </var-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <SearchBar @search="handleSearch" @clear="clearSearch" />

    <!-- 拖拽上传提示 -->
    <div
      v-if="isDragging"
      class="drag-overlay"
      @dragover.prevent
      @dragleave="handleDragLeave"
      @drop.prevent="handleDrop"
    >
      <div class="drag-content">
        <var-icon name="upload" :size="64" color="#3f51b5" />
        <p>松开鼠标上传文件</p>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div
      class="main-content"
      @dragenter.prevent="handleDragEnter"
    >
      <!-- 侧边栏 - 文件夹树 -->
      <div class="sidebar">
        <FolderTree ref="folderTreeRef" @select="handleFolderSelect" />
      </div>

      <!-- 文件列表区域 -->
      <div class="file-area">
        <!-- 面包屑导航 -->
        <Breadcrumb :path="currentPath" @navigate="handleNavigate" />

               <!-- 文件列表 -->
        <FileList
          :files="displayFiles"
          :loading="loading"
          :selected="selectedItems"
          @select="toggleSelect"
          @preview="handlePreview"
          @download="handleDownload"
          @rename="handleRename"
          @delete="handleDelete"
          @folder-click="handleFolderClick"
          @move="handleMove"
        />
      </div>
    </div>

    <!-- 上传对话框 -->
    <UploadDialog
      ref="uploadDialogRef"
      v-model:visible="showUploadDialog"
      :target-path="currentPath"
      @upload-complete="refreshFileList"
    />

    <!-- 新建文件夹对话框 -->
    <div v-if="showFolderDialog" class="custom-popup-overlay" @click.self="showFolderDialog = false">
      <div class="custom-popup">
        <h3>新建文件夹</h3>
        <input v-model="newFolderName" class="custom-input" placeholder="请输入文件夹名称" />
        <div class="dialog-actions">
          <var-button @click="showFolderDialog = false">取消</var-button>
          <var-button type="primary" @click="createFolder">确定</var-button>
        </div>
      </div>
    </div>

    <!-- 重命名对话框 -->
    <div v-if="showRenameDialog" class="custom-popup-overlay" @click.self="showRenameDialog = false">
      <div class="custom-popup">
        <h3>重命名</h3>
        <input v-model="renameName" class="custom-input" placeholder="请输入新名称" />
        <div class="dialog-actions">
          <var-button @click="showRenameDialog = false">取消</var-button>
          <var-button type="primary" @click="confirmRename">确定</var-button>
        </div>
      </div>
    </div>

    <!-- 预览对话框 -->
    <div v-if="showPreviewDialog" class="custom-popup-overlay" @click.self="showPreviewDialog = false">
      <div class="custom-popup preview-popup">
        <div class="preview-header">
          <span>{{ previewFile?.name }}</span>
          <var-icon name="close" @click="showPreviewDialog = false" />
        </div>
        <div class="preview-content">
          <img v-if="isImage" :src="previewUrl" alt="preview" />
          <video v-else-if="isVideo" :src="previewUrl" controls autoplay />
          <audio v-else-if="isAudio" :src="previewUrl" controls />
          <iframe v-else-if="isPdf" :src="previewUrl" frameborder="0" />
          <pre v-else-if="isText" class="text-preview">{{ textContent }}</pre>
          <div v-else class="unsupported">
            <var-icon name="file" :size="64" />
            <p>该文件类型不支持预览，请下载后查看</p>
            <button class="custom-button custom-button--primary" @click="downloadCurrent">下载文件</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 移动对话框 -->
    <div v-if="showMoveDialog" class="custom-popup-overlay" @click.self="showMoveDialog = false">
      <div class="custom-popup move-dialog">
        <h3>移动到</h3>
        <div class="folder-tree-container">
          <FolderTree 
            ref="moveFolderTreeRef" 
            :selected-path="moveToPath" 
            @select="handleMoveFolderSelect" 
          />
        </div>
        <div class="dialog-actions">
          <var-button @click="showMoveDialog = false">取消</var-button>
          <var-button type="primary" @click="confirmMove">确定</var-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { fileApi } from '@/api'
import { Snackbar, Dialog } from '@varlet/ui'
import FileList from '@/components/FileList.vue'
import Breadcrumb from '@/components/Breadcrumb.vue'
import FolderTree from '@/components/FolderTree.vue'
import SearchBar from '@/components/SearchBar.vue'
import StorageInfo from '@/components/StorageInfo.vue'
import UploadDialog from '@/components/UploadDialog.vue'

const router = useRouter()
const loading = ref(false)
const currentPath = ref('')
const files = ref([])
const searchQuery = ref('')
const selectedItems = ref([])

// UI 状态
const showUploadDialog = ref(false)
const uploadDialogRef = ref(null)
const folderTreeRef = ref(null)
const moveFolderTreeRef = ref(null)
const showFolderDialog = ref(false)
const showRenameDialog = ref(false)
const showPreviewDialog = ref(false)
const newFolderName = ref('')
const renameItem = ref(null)
const renameName = ref('')
const previewFile = ref(null)
const previewUrl = ref('')
const textContent = ref('')

// 移动相关状态
const showMoveDialog = ref(false)
const moveToPath = ref(undefined)
const folders = ref([])

// 暗色模式
const isDarkMode = ref(localStorage.getItem('dark_mode') === 'true')

// 初始化主题
if (isDarkMode.value) {
  document.documentElement.classList.add('dark')
} else {
  document.documentElement.classList.remove('dark')
}

// 计算属性
const displayFiles = computed(() => {
  if (!searchQuery.value) return files.value
  return files.value.filter(f =>
    f.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const isImage = computed(() => previewFile.value?.mime_type?.startsWith('image/'))
const isVideo = computed(() => previewFile.value?.mime_type?.startsWith('video/'))
const isAudio = computed(() => previewFile.value?.mime_type?.startsWith('audio/'))
const isPdf = computed(() => previewFile.value?.mime_type === 'application/pdf')
const isText = computed(() => previewFile.value?.mime_type?.startsWith('text/'))

// 加载文件列表
const refreshFileList = async () => {
  loading.value = true
  try {
    const res = await fileApi.getFiles(currentPath.value)
    files.value = res.files || []
    // 刷新文件夹树
    if (folderTreeRef.value && typeof folderTreeRef.value.refresh === 'function') {
      folderTreeRef.value.refresh()
    }
  } catch (error) {
    console.error('加载文件列表失败:', error)
    Snackbar.error('加载文件列表失败')
  } finally {
    loading.value = false
  }
}

// 创建文件夹
const createFolder = async () => {
  if (!newFolderName.value.trim()) {
    Snackbar.warning('请输入文件夹名称')
    return
  }

  try {
    const res = await fileApi.createFolder(currentPath.value, newFolderName.value)
    if (res.success) {
      Snackbar.success('文件夹创建成功')
      showFolderDialog.value = false
      newFolderName.value = ''
      refreshFileList()
      // 刷新文件夹树
      if (folderTreeRef.value && typeof folderTreeRef.value.refresh === 'function') {
        folderTreeRef.value.refresh()
      }
    } else {
      Snackbar.error(res.error || '创建失败')
    }
  } catch (error) {
    Snackbar.error('创建文件夹失败')
  }
}

// 删除单个文件/文件夹
const handleDelete = (item) => {
  Dialog({
    title: '确认删除',
    message: `确定删除 ${item.name} 吗？`,
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    onConfirm: async () => {
      try {
        console.log('[删除] 删除单个:', item.path)
        const res = await fileApi.deleteItems([item.path])
        console.log('[删除] 结果:', res)
        if (res.success && res.success.length > 0) {
          Snackbar.success('删除成功')
          refreshFileList()
        } else {
          Snackbar.error(res.failed?.[0]?.reason || '删除失败')
        }
      } catch (error) {
        console.error('[删除] 错误:', error)
        Snackbar.error('删除失败')
      }
    }
  })
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedItems.value.length === 0) {
    Snackbar.warning('请先选择要删除的项目')
    return
  }

  Dialog({
    title: '确认批量删除',
    message: `确定删除 ${selectedItems.value.length} 个项目吗？此操作不可撤销！`,
    confirmButtonText: '确定删除',
    cancelButtonText: '取消',
    confirmButtonColor: '#f44336',
    onConfirm: async () => {
      const paths = selectedItems.value.map(i => i.path)
      console.log('[批量删除] 删除路径:', paths)
      try {
        const res = await fileApi.deleteItems(paths)
        console.log('[批量删除] 结果:', res)
        if (res.success && res.success.length > 0) {
          Snackbar.success(`成功删除 ${res.success.length} 个项目`)
          selectedItems.value = []
          refreshFileList()
        } else {
          Snackbar.error('删除失败')
        }
      } catch (error) {
        console.error('[批量删除] 错误:', error)
        Snackbar.error('删除失败')
      }
    }
  })
}

// 重命名
const handleRename = (item) => {
  renameItem.value = item
  renameName.value = item.name
  showRenameDialog.value = true
}

const confirmRename = async () => {
  if (!renameName.value.trim()) {
    Snackbar.warning('请输入新名称')
    return
  }

  try {
    const res = await fileApi.rename(renameItem.value.path, renameName.value)
    if (res.success) {
      Snackbar.success('重命名成功')
      showRenameDialog.value = false
      refreshFileList()
    } else {
      Snackbar.error(res.error || '重命名失败')
    }
  } catch (error) {
    Snackbar.error('重命名失败')
  }
}

// 预览文件
const handlePreview = async (item) => {
  previewFile.value = item
  previewUrl.value = fileApi.preview(item.path)
  textContent.value = ''

  // 检查文件类型并处理预览
  const mime_type = item.mime_type || 'application/octet-stream'
  const isTextFile = mime_type.startsWith('text/') || mime_type === 'application/json'

  if (isTextFile) {
    try {
      const response = await fetch(previewUrl.value)
      if (response.ok) {
        textContent.value = await response.text()
      } else {
        textContent.value = '无法加载文件内容'
      }
    } catch (error) {
      console.error('预览文本文件失败:', error)
      textContent.value = '无法加载文件内容'
    }
  }

  showPreviewDialog.value = true
}

// 下载文件
const handleDownload = (item) => {
  const url = fileApi.download(item.path)
  const a = document.createElement('a')
  a.href = url
  a.download = item.name
  a.click()
}

const downloadCurrent = () => {
  if (previewFile.value) {
    handleDownload(previewFile.value)
  }
}

// 选择文件
const toggleSelect = (item) => {
  if (item === null) {
    // 取消全选
    selectedItems.value = []
  } else if (item.type === 'select-all') {
    // 全选所有文件
    selectedItems.value = [...item.files]
  } else {
    const index = selectedItems.value.findIndex(i => i.path === item.path)
    if (index > -1) {
      selectedItems.value.splice(index, 1)
    } else {
      selectedItems.value.push(item)
    }
  }
}

// 文件夹点击
const handleFolderClick = (item) => {
  if (item.is_dir) {
    currentPath.value = item.path
    refreshFileList()
  }
}

// 面包屑导航
const handleNavigate = (path) => {
  currentPath.value = path
  refreshFileList()
}

// 文件夹树选择
const handleFolderSelect = (path) => {
  currentPath.value = path
  refreshFileList()
}

// 搜索
const handleSearch = (query) => {
  searchQuery.value = query
  if (query) {
    fileApi.search(query, currentPath.value).then(res => {
      files.value = res.files || []
    })
  } else {
    refreshFileList()
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  refreshFileList()
}

// 移动相关函数
const loadFolders = async () => {
  try {
    const res = await fileApi.getFolderTree('')
    folders.value = res.folders || []
  } catch (error) {
    console.error('加载文件夹列表失败:', error)
  }
}

const handleMoveFolderSelect = (path) => {
  moveToPath.value = path
}

const handleMove = async (moveData) => {
  try {
    const res = await fileApi.moveItems(moveData.sources, moveData.destination)
    if (res.success && res.success.length > 0) {
      Snackbar.success('移动成功')
      refreshFileList()
    } else if (res.failed && res.failed.length > 0) {
      Snackbar.error(res.failed[0].reason || '移动失败')
    } else {
      Snackbar.success('移动成功')
      refreshFileList()
    }
  } catch (error) {
    console.error('移动失败:', error)
    Snackbar.error('移动失败')
  }
}

const confirmMove = async () => {
  if (moveToPath.value === undefined || moveToPath.value === null) {
    Snackbar.warning('请选择目标文件夹')
    return
  }

  const paths = selectedItems.value.map(i => i.path)
  try {
    const res = await fileApi.moveItems(paths, moveToPath.value)
    if (res.success && res.success.length > 0) {
      Snackbar.success('移动成功')
      showMoveDialog.value = false
      selectedItems.value = []
      refreshFileList()
    } else if (res.failed && res.failed.length > 0) {
      Snackbar.error(res.failed[0].reason || '移动失败')
    } else {
      Snackbar.success('移动成功')
      showMoveDialog.value = false
      selectedItems.value = []
      refreshFileList()
    }
  } catch (error) {
    console.error('移动失败:', error)
    Snackbar.error('移动失败')
  }
}

// 暗色模式
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  localStorage.setItem('dark_mode', isDarkMode.value)
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// 跳转管理页面
const goToAdmin = () => {
  router.push('/admin')
}

// 拖拽上传
const isDragging = ref(false)
let dragCounter = 0

const handleDragEnter = (e) => {
  dragCounter++
  if (e.dataTransfer.types.includes('Files')) {
    isDragging.value = true
  }
}

const handleDragLeave = (e) => {
  dragCounter--
  if (dragCounter === 0) {
    isDragging.value = false
  }
}

const handleDrop = async (e) => {
  dragCounter = 0
  isDragging.value = false

  const items = e.dataTransfer.items
  if (!items || items.length === 0) return

  const files = []
  const traverseFileTree = (item, path = '') => {
    return new Promise((resolve) => {
      if (item.isFile) {
        item.file((file) => {
          file.relativePath = path + file.name
          files.push(file)
          resolve()
        })
      } else if (item.isDirectory) {
        const dirReader = item.createReader()
        dirReader.readEntries(async (entries) => {
          for (const entry of entries) {
            await traverseFileTree(entry, path + item.name + '/')
          }
          resolve()
        })
      } else {
        resolve()
      }
    })
  }

  // 处理所有拖拽项
  for (let i = 0; i < items.length; i++) {
    const item = items[i].webkitGetAsEntry()
    if (item) {
      await traverseFileTree(item)
    }
  }

  if (files.length > 0) {
    // 打开上传对话框并添加文件
    showUploadDialog.value = true
    // 延迟执行，等待对话框打开
    setTimeout(() => {
      if (uploadDialogRef.value) {
        uploadDialogRef.value.addFiles(files)
      }
    }, 100)
  }
}

// 键盘事件
const handleKeydown = (e) => {
  if (e.key === 'Backspace') {
    if (currentPath.value) {
      const parentPath = currentPath.value.split('/').slice(0, -1).join('/')
      handleNavigate(parentPath)
    }
  }
}

onMounted(() => {
  refreshFileList()
  loadFolders()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.file-manager {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.dark .file-manager {
  background-color: #1a1a2e;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.dark .header {
  background-color: #2a2a3a;
  border-bottom: 1px solid #3a3a4a;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: bold;
  color: #3f51b5;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.theme-switch {
  display: flex;
  align-items: center;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background-color: #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
}

.theme-toggle:hover {
  background-color: #e0e0e0;
}

.theme-toggle.dark {
  background-color: #333;
}

.theme-toggle.dark:hover {
  background-color: #444;
}

.custom-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background-color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.dark .custom-button {
  background-color: #2a2a3a;
  border-color: #4a4a5a;
  color: #fff;
}

.custom-button:hover {
  background-color: #f5f5f5;
}

.dark .custom-button:hover {
  background-color: #353545;
}

.custom-button--primary {
  background-color: #3f51b5;
  border-color: #3f51b5;
  color: #fff;
}

.custom-button--primary:hover {
  background-color: #303f9f;
}

.custom-button--danger {
  background-color: #f44336;
  border-color: #f44336;
  color: #fff;
}

.custom-button--danger:hover {
  background-color: #d32f2f;
}

.custom-button--text {
  border: none;
  background: transparent;
}

.main-content {
  display: flex;
  padding: 24px;
  gap: 24px;
}

.sidebar {
  width: 280px;
  flex-shrink: 0;
}

.file-area {
  flex: 1;
  min-width: 0;
}

.storage-card {
  margin-bottom: 16px;
}

.custom-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.custom-popup {
  background-color: #fff;
  border-radius: 12px;
  padding: 24px;
  width: 400px;
  max-width: 90vw;
}

.dark .custom-popup {
  background-color: #2a2a3a;
}

.preview-popup {
  width: 80vw;
  height: 80vh;
  display: flex;
  flex-direction: column;
  padding: 0;
}

.custom-popup h3 {
  margin-bottom: 20px;
  text-align: center;
}

.custom-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
}

.dark .custom-input {
  background-color: #1e1e2a;
  border-color: #4a4a5a;
  color: #fff;
}

.custom-input:focus {
  outline: none;
  border-color: #3f51b5;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
}

.preview-header var-icon {
  cursor: pointer;
  font-size: 20px;
}

.preview-content {
  flex: 1;
  overflow: auto;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.preview-content iframe {
  flex: 1;
  width: 100%;
  height: 100%;
  border: none;
}

.preview-content img,
.preview-content video,
.preview-content iframe {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.preview-content iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.text-preview {
  width: 100%;
  height: 100%;
  padding: 16px;
  overflow: auto;
  white-space: pre-wrap;
  font-family: monospace;
  background-color: #fff;
}

.unsupported {
  text-align: center;
  color: #999;
}

.unsupported var-icon {
  margin-bottom: 16px;
}

.drag-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(63, 81, 181, 0.9);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
  animation: fadeIn 0.2s ease;
}

.drag-content {
  text-align: center;
  color: #fff;
}

.drag-content p {
  margin-top: 16px;
  font-size: 20px;
  font-weight: 500;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.folder-selector {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 20px;
}

.dark .folder-selector {
  border-color: #4a4a5a;
}

.folder-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.dark .folder-item {
  border-bottom-color: #3a3a4a;
}

.folder-item:hover {
  background-color: #f5f5f5;
}

.dark .folder-item:hover {
  background-color: #353545;
}

.folder-item.active {
  background-color: #e8eaf6;
}

.dark .folder-item.active {
  background-color: #3f51b5;
}

.folder-item var-icon {
  color: #ff9800;
}

.move-dialog {
  width: 500px;
  max-width: 90vw;
}

.folder-tree-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-bottom: 20px;
}

.dark .folder-tree-container {
  border-color: #4a4a5a;
}

@media (max-width: 768px) {
  .sidebar {
    display: none;
  }

  .header-actions {
    gap: 8px;
  }

  .main-content {
    padding: 12px;
  }

  .custom-button span {
    display: none;
  }
}
</style>