<!-- src/views/client/FileManager.vue -->
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

    <!-- 现代化预览对话框 - 优化音乐播放器界面 -->
   <div v-if="showPreviewDialog" class="custom-popup-overlay" @click.self="closePreview">
  <div class="custom-popup preview-popup modern-preview">
    <div class="preview-header">
      <div class="preview-title">
        <var-icon :name="getPreviewIcon()" :size="24" />
        <span>{{ previewFile?.name }}</span>
      </div>
      <var-icon name="close" class="close-icon" @click="closePreview" :size="24" />
    </div>
    <div class="preview-content">
      <!-- 图片预览 -->
      <img v-if="isImage" :src="previewUrl" alt="preview" class="preview-media" />

      <!-- 视频预览 -->
      <video v-else-if="isVideo" :src="previewUrl" controls autoplay class="preview-media" />

      <!-- 音频预览 - 现代化音乐播放器 -->
      <div v-else-if="isAudio" class="audio-preview-modern">
        <div class="audio-artwork">
          <div class="album-art">
            <var-icon name="music" :size="80" class="music-icon" />
            <div class="wave-animation" v-if="isPlaying">
              <span></span><span></span><span></span><span></span>
            </div>
          </div>
        </div>
        <div class="audio-info">
          <h3 class="audio-title">{{ previewFile?.name }}</h3>
          <p class="audio-meta">{{ formatFileSize(previewFile?.size) }} · 音频文件</p>
        </div>
        <div class="audio-player-controls">
          <div class="time-display">
            <span>{{ formatTime(currentTime) }}</span>
            <span>{{ formatTime(duration) }}</span>
          </div>
          <input
            type="range"
            class="audio-progress"
            v-model="progressPercent"
            @input="seekAudio"
            :style="{ backgroundSize: progressPercent + '% 100%' }"
          />
          <div class="control-buttons">
            <!-- 播放/暂停按钮 - 根据状态显示不同图标 -->
            <button class="control-btn" @click="togglePlayPause">
              <var-icon :name="isPlaying ? 'pause-circle' : 'play-circle'" :size="48" />
            </button>
          </div>
        </div>
        <audio
          ref="audioElement"
          :src="previewUrl"
          @timeupdate="updateTime"
          @loadedmetadata="onLoadedMetadata"
          @ended="onAudioEnded"
          @play="handlePlay"
          @pause="handlePause"
          @error="handleAudioError"
        ></audio>
      </div>

      <!-- PDF预览 -->
      <iframe v-else-if="isPdf" :src="previewUrl" frameborder="0" class="preview-media" />

      <!-- 文本预览 -->
      <pre v-else-if="isText" class="text-preview">{{ textContent }}</pre>

      <!-- 不支持的类型 -->
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

// 音频播放器状态
const audioElement = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const progressPercent = ref(0)

// 移动相关状态
const showMoveDialog = ref(false)
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

const isImage = computed(() => previewFile.value?.mime_type?.startsWith('image/'))
const isVideo = computed(() => previewFile.value?.mime_type?.startsWith('video/'))
const isAudio = computed(() => previewFile.value?.mime_type?.startsWith('audio/'))
const isPdf = computed(() => previewFile.value?.mime_type === 'application/pdf')
const isText = computed(() => previewFile.value?.mime_type?.startsWith('text/'))

// 获取预览图标
const getPreviewIcon = () => {
  if (isImage.value) return 'image'
  if (isVideo.value) return 'video'
  if (isAudio.value) return 'music'
  if (isPdf.value) return 'file-pdf'
  if (isText.value) return 'file-text'
  return 'file'
}

// 格式化文件大小
const formatFileSize = (size) => {
  if (!size) return '未知大小'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(2)} KB`
  if (size < 1024 * 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(2)} MB`
  return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

// 格式化时间
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 音频播放控制
const togglePlayPause = () => {
  if (!audioElement.value) return
  if (isPlaying.value) {
    audioElement.value.pause()
  } else {
    audioElement.value.play()
  }
}

const handlePlay = () => {
  isPlaying.value = true
}

const handlePause = () => {
  isPlaying.value = false
}

const handleAudioError = (e) => {
  console.error('音频播放错误:', e)
  Snackbar.error('音频加载失败，请检查文件格式')
  isPlaying.value = false
}

const updateTime = () => {
  if (audioElement.value) {
    currentTime.value = audioElement.value.currentTime
    progressPercent.value = (currentTime.value / duration.value) * 100
  }
}

const onLoadedMetadata = () => {
  if (audioElement.value) {
    duration.value = audioElement.value.duration
  }
}

const onAudioEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
  progressPercent.value = 0
  if (audioElement.value) {
    audioElement.value.currentTime = 0
  }
}

const seekAudio = () => {
  if (audioElement.value && duration.value) {
    const newTime = (progressPercent.value / 100) * duration.value
    audioElement.value.currentTime = newTime
    currentTime.value = newTime
  }
}

// 关闭预览并停止音频
const closePreview = () => {
  if (audioElement.value) {
    audioElement.value.pause()
    isPlaying.value = false
  }
  showPreviewDialog.value = false
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

// 预览文件
const handlePreview = async (item) => {
  // 关闭之前的音频播放
  if (audioElement.value) {
    audioElement.value.pause()
    isPlaying.value = false
  }

  previewFile.value = item
  previewUrl.value = fileApi.preview(item.path)
  textContent.value = ''

  // 重置音频状态
  currentTime.value = 0
  duration.value = 0
  progressPercent.value = 0

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
  }
}

const downloadCurrent = () => {
  if (previewFile.value) {
    handleDownload(previewFile.value)
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
  if (audioElement.value) {
    audioElement.value.pause()
  }
})
</script>

<style scoped>
/* 保持原有样式，并添加音频播放器现代化样式 */

/* 现代化音乐播放器样式 */
.audio-preview-modern {
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
  padding: 32px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 24px;
  color: white;
  text-align: center;
  box-shadow: 0 20px 35px -10px rgba(0, 0, 0, 0.3);
}

.dark .audio-preview-modern {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
}

.audio-artwork {
  margin-bottom: 24px;
}

.album-art {
  position: relative;
  width: 140px;
  height: 140px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.music-icon {
  color: white;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
}

.wave-animation {
  position: absolute;
  bottom: -20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 4px;
}

.wave-animation span {
  width: 4px;
  height: 20px;
  background: white;
  border-radius: 2px;
  animation: wave 1s ease-in-out infinite;
}

.wave-animation span:nth-child(2) { animation-delay: 0.1s; }
.wave-animation span:nth-child(3) { animation-delay: 0.2s; }
.wave-animation span:nth-child(4) { animation-delay: 0.3s; }

@keyframes wave {
  0%, 100% { height: 8px; }
  50% { height: 24px; }
}

.audio-info {
  margin-bottom: 24px;
}

.audio-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
  word-break: break-all;
}

.audio-meta {
  font-size: 13px;
  opacity: 0.8;
}

.audio-player-controls {
  width: 100%;
}

.time-display {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 8px;
  opacity: 0.8;
}

.audio-progress {
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.3);
  -webkit-appearance: none;
  appearance: none;
  margin-bottom: 20px;
}

.audio-progress::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.audio-progress::-webkit-slider-runnable-track {
  height: 4px;
  background: linear-gradient(to right, white var(--progress, 0%), rgba(255, 255, 255, 0.3) var(--progress, 0%));
  border-radius: 2px;
}

.control-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.control-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

/* 现代化预览对话框 */
.modern-preview {
  border-radius: 32px !important;
  overflow: hidden;
  padding: 0 !important;
  width: 90vw;
  max-width: 800px;
  background: #fff !important;
}

.dark .modern-preview {
  background: #1e1e2a !important;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.05);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.dark .preview-header {
  background: rgba(255, 255, 255, 0.05);
  border-bottom-color: rgba(255, 255, 255, 0.1);
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 500;
}

.close-icon {
  cursor: pointer;
  transition: opacity 0.2s;
}

.close-icon:hover {
  opacity: 0.7;
}

.preview-content {
  padding: 24px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
}

.dark .preview-content {
  background: #1a1a2e;
}

.preview-media {
  max-width: 100%;
  max-height: 60vh;
  border-radius: 12px;
}

.text-preview {
  width: 100%;
  max-height: 60vh;
  overflow: auto;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  background: #1e1e2e;
  color: #e0e0e0;
  border-radius: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.unsupported {
  text-align: center;
  color: #94a3b8;
}

.unsupported var-icon {
  margin-bottom: 16px;
}

/* 其他样式保持原有 */
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
</style>