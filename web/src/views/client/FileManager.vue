<template>
  <div class="file-manager">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="logo">
        <img src="../../icons/icon.ico" width="30" alt="logo">
        <span>AuroraShare · 极光共享</span>
      </div>
      <div class="header-actions">
        <!-- 移动端折叠按钮 -->
        <var-button
          class="mobile-actions-toggle"
          @click="toggleMobileActions"
          round
          text
        >
          <var-icon :name="mobileActionsVisible ? 'close' : 'menu'" />
        </var-button>

        <!-- 操作按钮组 - 可折叠 -->
        <div class="actions-group" :class="{ 'mobile-visible': mobileActionsVisible }">
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
            <img v-if="!isDarkMode" src="/src/icons/sun.svg" alt="Sun" style="width: 20px; height: 20px;" />
            <img v-else src="/src/icons/moon.svg" alt="Moon" style="width: 20px; height: 20px;" />
          </var-button>
          <var-button class="custom-button custom-button--text" @click="goToAdmin">
            <var-icon name="settings" /> 管理
          </var-button>
        </div>
      </div>
    </div>

    <!-- 移动端遮罩层 -->
    <div
      v-if="mobileActionsVisible"
      class="mobile-actions-overlay"
      @click="toggleMobileActions"
    ></div>

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
      :class="{ 'sidebar-collapsed': sidebarCollapsed }"
      @dragenter.prevent="handleDragEnter"
    >
      <!-- 侧边栏 - 文件夹树（可折叠） -->
      <div class="sidebar" :class="{ 'collapsed': sidebarCollapsed }">
        <div class="sidebar-header" v-if="!sidebarCollapsed">
          <span class="sidebar-title">文件夹</span>
          <var-button class="collapse-btn" @click="toggleSidebar" text round size="small">
            <var-icon name="chevron-left" />
          </var-button>
        </div>
        <div class="sidebar-content" v-show="!sidebarCollapsed">
          <FolderTree ref="folderTreeRef" @select="handleFolderSelect" />
        </div>
        <!-- 折叠状态下的快捷按钮 -->
        <div class="sidebar-collapsed-actions" v-if="sidebarCollapsed">
          <div class="collapsed-item" @click="toggleSidebar" title="展开文件夹">
            <var-icon name="chevron-right" :size="20" />
          </div>
          <div class="collapsed-item" @click="refreshFileList" title="刷新">
            <var-icon name="refresh" :size="20" />
          </div>
          <div class="collapsed-item" @click="handleNavigate('')" title="根目录">
            <var-icon name="home" :size="20" />
          </div>
        </div>
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
          :search-keyword="searchQuery"
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
const showMoveDialog = ref(false)
const newFolderName = ref('')
const renameItem = ref(null)
const renameName = ref('')
const moveToPath = ref(undefined)
const folders = ref([])

// 侧边栏折叠状态
const sidebarCollapsed = ref(localStorage.getItem('sidebar_collapsed') === 'true')

// 移动端操作按钮折叠状态
const mobileActionsVisible = ref(false)

// 暗色模式
const isDarkMode = ref(localStorage.getItem('dark_mode') === 'true')

// 初始化主题
if (isDarkMode.value) {
  document.documentElement.classList.add('dark')
} else {
  document.documentElement.classList.remove('dark')
}

// 切换移动端操作按钮显示
const toggleMobileActions = () => {
  mobileActionsVisible.value = !mobileActionsVisible.value
}

// 侧边栏折叠切换
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar_collapsed', sidebarCollapsed.value)
}

// 计算属性
const displayFiles = computed(() => {
  if (!searchQuery.value) return files.value
  return files.value.filter(f =>
    f.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

// 格式化文件大小
const formatFileSize = (size) => {
  if (!size) return '未知大小'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

// 预览文件 - 支持预览的在新窗口打开，不支持的自动下载
const handlePreview = async (item) => {
  const previewUrl = fileApi.preview(item.path)

  // 定义不支持预览的文件类型
  const unsupportedPreviewTypes = [
    'application/vnd.openxmlformats-officedocument',
    'application/msword',
    'application/vnd.ms-excel',
    'application/vnd.ms-powerpoint',
    'application/zip',
    'application/x-rar',
    'application/x-7z',
    'application/x-rar-compressed',
    'application/x-zip-compressed',
    'application/octet-stream'
  ]

  const mimeType = item.mime_type || ''
  const isUnsupportedPreview = unsupportedPreviewTypes.some(type => mimeType.includes(type))

  // 对于 Office 文档、压缩包等不支持预览的文件类型
  if (isUnsupportedPreview || (!mimeType.startsWith('image/') &&
      !mimeType.startsWith('video/') &&
      !mimeType.startsWith('audio/') &&
      !mimeType.startsWith('text/') &&
      mimeType !== 'application/pdf')) {
    // 不支持预览，直接下载
    const a = document.createElement('a')
    a.href = previewUrl
    a.download = item.name
    a.click()
    Snackbar.info(`${item.name} 不支持预览，已开始下载`)
  } else {
    // 支持预览的文件在新窗口打开
    window.open(previewUrl, '_blank')
    Snackbar.info(`正在新窗口打开: ${item.name}`)
  }
}

// 下载文件或文件夹
const handleDownload = async (item) => {
  if (item.is_dir) {
    try {
      const response = await fileApi.downloadFolder(item.path)
      const blob = new Blob([response], { type: 'application/zip' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${item.name}.zip`
      a.click()
      URL.revokeObjectURL(url)
      Snackbar.success('文件夹下载已开始')
    } catch (error) {
      console.error('下载文件夹失败:', error)
      Snackbar.error('下载文件夹失败')
    }
  } else {
    const url = fileApi.download(item.path)
    const a = document.createElement('a')
    a.href = url
    a.download = item.name
    a.click()
    Snackbar.success('文件下载已开始')
  }
}

// 选择文件
const toggleSelect = (item) => {
  if (item === null) {
    selectedItems.value = []
  } else if (item.type === 'select-all') {
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

// 加载文件列表
const refreshFileList = async () => {
  loading.value = true
  try {
    const res = await fileApi.getFiles(currentPath.value)
    files.value = res.files || []
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
        const res = await fileApi.deleteItems([item.path])
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
      try {
        const res = await fileApi.deleteItems(paths)
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

  for (let i = 0; i < items.length; i++) {
    const item = items[i].webkitGetAsEntry()
    if (item) {
      await traverseFileTree(item)
    }
  }

  if (files.length > 0) {
    showUploadDialog.value = true
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
/* 所有样式保持不变，但移除了预览对话框相关的样式 */
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
  position: relative;
}

/* 移动端操作按钮折叠按钮 */
.mobile-actions-toggle {
  display: none;
}

/* 操作按钮组 */
.actions-group {
  display: flex;
  align-items: center;
  gap: 12px;
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
  transition: all 0.3s ease;
}

/* 侧边栏样式 */
.sidebar {
  width: 280px;
  flex-shrink: 0;
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.dark .sidebar {
  background-color: #2a2a3a;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.sidebar.collapsed {
  width: 60px;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.dark .sidebar-header {
  border-bottom-color: #3a3a4a;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.dark .sidebar-title {
  color: #fff;
}

.collapse-btn {
  padding: 4px;
  cursor: pointer;
}

.sidebar-content {
  height: calc(100vh - 180px);
  overflow-y: auto;
}

/* 折叠状态下的快捷操作栏 */
.sidebar-collapsed-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
}

.collapsed-item {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
}

.dark .collapsed-item {
  color: #aaa;
}

.collapsed-item:hover {
  background-color: #f0f0f0;
  color: #3f51b5;
}

.dark .collapsed-item:hover {
  background-color: #3a3a4a;
  color: #7986cb;
}

.file-area {
  flex: 1;
  min-width: 0;
}

/* 移动端遮罩层 */
.mobile-actions-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 99;
  display: none;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header {
    padding: 12px 16px;
  }

  .logo span {
    display: none;
  }

  .mobile-actions-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background-color: #f0f0f0;
    border-radius: 50%;
    cursor: pointer;
  }

  .dark .mobile-actions-toggle {
    background-color: #3a3a4a;
    color: #fff;
  }

  .actions-group {
    position: fixed;
    top: 60px;
    right: -100%;
    width: 280px;
    flex-direction: column;
    align-items: stretch;
    background-color: #fff;
    border-radius: 12px;
    padding: 16px;
    gap: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transition: right 0.3s ease;
    z-index: 100;
  }

  .dark .actions-group {
    background-color: #2a2a3a;
    border: 1px solid #3a3a4a;
  }

  .actions-group.mobile-visible {
    right: 16px;
  }

  .mobile-actions-overlay {
    display: block;
  }

  .custom-button {
    width: 100%;
    justify-content: center;
  }

  .theme-toggle {
    width: 100%;
    border-radius: 8px;
    background-color: #f0f0f0;
  }

  .dark .theme-toggle {
    background-color: #3a3a4a;
  }

  .sidebar {
    position: fixed;
    left: 0;
    top: 60px;
    bottom: 0;
    z-index: 99;
    transform: translateX(0);
    transition: transform 0.3s ease;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  }

  .sidebar.collapsed {
    transform: translateX(-100%);
    width: 280px;
  }

  .main-content {
    padding: 12px;
  }

  .main-content.sidebar-collapsed .file-area {
    width: 100%;
  }
}

/* 平板适配 */
@media (min-width: 769px) and (max-width: 1024px) {
  .custom-button span {
    display: inline-block;
  }

  .custom-button {
    padding: 8px 12px;
  }

  .sidebar {
    width: 240px;
  }

  .main-content.sidebar-collapsed .sidebar {
    width: 60px;
  }

  .main-content.sidebar-collapsed .file-area {
    width: calc(100% - 84px);
  }
}

/* 桌面端折叠时调整布局 */
@media (min-width: 1025px) {
  .main-content.sidebar-collapsed .sidebar {
    width: 60px;
  }

  .main-content.sidebar-collapsed .file-area {
    width: calc(100% - 84px);
  }
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
</style>