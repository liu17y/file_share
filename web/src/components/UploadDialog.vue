<!-- src/components/UploadDialog.vue -->
<template>
  <var-popup
    v-model:show="visible"
    position="center"
    :style="{ width: '600px', maxWidth: '90vw' }"
  >
    <div class="upload-dialog">
      <div class="dialog-header">
        <h3>上传文件</h3>
        <div class="header-right">
          <div v-if="uploading" class="upload-speed">
            上传速度: {{ uploadSpeed }}/s
          </div>
          <var-icon name="close" @click="close" />
        </div>
      </div>

      <div 
        class="upload-area" 
        @dragover.prevent @drop.prevent="handleDrop"
        @dragenter.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        :class="{ 'drag-over': isDragging }"
      >
        <var-icon name="upload" :size="48" />
        <p v-if="!isDragging">拖拽文件或文件夹到此区域</p>
        <p v-else class="drag-hint">松开鼠标开始上传</p>
        <div class="upload-buttons">
          <var-button type="primary" size="small" @click="selectFiles">
            <var-icon name="file-upload" /> 选择文件
          </var-button>
          <var-button type="info" size="small" @click="selectFolder">
            <var-icon name="folder-upload" /> 选择文件夹
          </var-button>
        </div>
        <input
          ref="fileInput"
          type="file"
          multiple
          style="display: none"
          @change="handleFileSelect"
        />
        <input
          ref="folderInput"
          type="file"
          webkitdirectory
          directory
          style="display: none"
          @change="handleFolderSelect"
        />
      </div>

      <div v-if="uploading" class="upload-controls">
        <var-button v-if="!paused" size="small" @click="pauseUpload">
          <var-icon name="pause" />
          暂停
        </var-button>
        <var-button v-else size="small" @click="resumeUpload">
          <var-icon name="play" />
          继续
        </var-button>
      </div>

      <div class="upload-list">
        <div
          v-for="task in uploadTasks"
          :key="task.id"
          class="upload-item"
        >
          <div class="item-info">
            <var-icon :name="getFileIcon(task.relativePath || task.file.name)" />
            <div class="info">
              <div class="name">{{ task.relativePath || task.file.name }}</div>
              <div class="size">{{ formatSize(task.file.size) }}</div>
            </div>
          </div>
          <div class="item-progress">
            <var-progress
              :percentage="task.progress"
              :color="task.status === 'error' ? '#f44336' : '#3f51b5'"
            />
            <div class="status">
              <span v-if="task.status === 'uploading'">{{ task.progress }}%</span>
              <span v-else-if="task.status === 'success'" class="success">
                <var-icon name="check-circle" /> 完成
              </span>
              <span v-else-if="task.status === 'error'" class="error">
                <var-icon name="error" /> {{ task.error || '上传失败' }}
              </span>
              <span v-else-if="task.status === 'waiting'" class="waiting">
                等待中
              </span>
            </div>
            <var-button
              v-if="task.status === 'error'"
              size="small"
              text
              @click="retryUpload(task)"
            >
              <var-icon name="refresh" />
            </var-button>
            <var-button
              v-if="task.status === 'uploading'"
              size="small"
              text
              @click="cancelUpload(task)"
            >
              <var-icon name="close" />
            </var-button>
          </div>
        </div>
      </div>

      <div class="dialog-footer">
        <var-button @click="close">关闭</var-button>
        <var-button
          v-if="uploadTasks.length > 0"
          type="primary"
          @click="startUpload"
        >
          开始上传
        </var-button>
      </div>
    </div>
  </var-popup>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { uploadApi } from '@/api'
import { Snackbar } from '@varlet/ui'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  targetPath: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:visible', 'upload-complete'])

const visible = ref(props.visible)
const fileInput = ref(null)
const folderInput = ref(null)
const uploadTasks = ref([])
const isDragging = ref(false)
const uploading = ref(false)
const paused = ref(false)
const uploadSpeed = ref('0 B')
const lastUploadedBytes = ref(0)
const lastSpeedTime = ref(Date.now())
const speedInterval = ref(null)
const uploadTasksMap = ref(new Map()) // 存储上传任务的XHR

const CHUNK_SIZE = 2 * 1024 * 1024 // 2MB
const MAX_CONCURRENT = 6 // 最大并发分片数
const MAX_RETRY = 3 // 最大重试次数

watch(() => props.visible, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:visible', val)
})

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    pdf: 'file-pdf',
    jpg: 'file-image',
    png: 'file-image',
    mp4: 'file-video',
    mp3: 'file-music',
    zip: 'file-zip'
  }
  return iconMap[ext] || 'file'
}

const selectFiles = () => {
  fileInput.value.click()
}

const selectFolder = () => {
  folderInput.value.click()
}

const handleFolderSelect = (e) => {
  const files = Array.from(e.target.files)
  // 保留相对路径信息
  addFiles(files, true)
  folderInput.value.value = ''
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  addFiles(files, true)
  fileInput.value.value = ''
}

const handleDrop = (e) => {
  const files = Array.from(e.dataTransfer.files)
  addFiles(files, true)
}

const addFiles = (files, keepPath = false) => {
  for (const file of files) {
    const task = {
      id: `${Date.now()}-${Math.random()}`,
      file: file,
      status: 'pending',
      progress: 0,
      uploadedChunks: [],
      totalChunks: Math.ceil(file.size / CHUNK_SIZE),
      abortController: null,
      relativePath: keepPath ? file.webkitRelativePath || file.name : file.name
    }
    uploadTasks.value.push(task)
  }
}

const startUpload = () => {
  uploading.value = true
  paused.value = false
  
  // 开始计算上传速度
  startSpeedCalculation()
  
  const pendingTasks = uploadTasks.value.filter(task => task.status === 'pending')
  
  if (pendingTasks.length === 0) {
    uploading.value = false
    stopSpeedCalculation()
    return
  }
  
  // 并发上传文件
  const CONCURRENT_FILES = 3
  const processFiles = async () => {
    for (let i = 0; i < pendingTasks.length; i += CONCURRENT_FILES) {
      if (paused.value) break
      
      const batch = pendingTasks.slice(i, i + CONCURRENT_FILES)
      await Promise.all(batch.map(task => uploadFile(task)))
    }
    
    uploading.value = false
    stopSpeedCalculation()
  }
  
  processFiles()
}

const uploadFile = async (task) => {
  task.status = 'uploading'
  task.abortController = new AbortController()

  return new Promise(async (resolve, reject) => {
    try {
      // 使用相对路径作为文件名，保持目录结构
      const fileName = task.relativePath || task.file.name
      
      // 1. 初始化上传
      const initFormData = new FormData()
      initFormData.append('file_id', task.id)
      initFormData.append('file_name', fileName)
      initFormData.append('file_size', task.file.size)
      initFormData.append('target_path', props.targetPath)
      initFormData.append('total_chunks', task.totalChunks)

      const initRes = await uploadApi.initUpload(
        task.id,
        fileName,
        task.file.size,
        props.targetPath,
        task.totalChunks
      )

      if (initRes.error) {
        throw new Error(initRes.error)
      }

      const uploadedChunks = new Set(initRes.uploaded_chunks || [])
      task.uploadedChunks = Array.from(uploadedChunks)
      task.completedChunks = uploadedChunks.size
      task.progress = Math.floor((task.completedChunks / task.totalChunks) * 100)

      // 2. 准备需要上传的分片
      const chunks = []
      for (let chunkIndex = 0; chunkIndex < task.totalChunks; chunkIndex++) {
        if (!uploadedChunks.has(chunkIndex)) {
          chunks.push(chunkIndex)
        }
      }

      if (chunks.length === 0) {
        task.status = 'success'
        task.progress = 100
        Snackbar.success(`${task.file.name} 上传成功`)
        emit('upload-complete')
        resolve()
        return
      }

      // 3. 使用队列控制并发上传分片
      let completedChunks = uploadedChunks.size
      const queue = [...chunks]
      const activeUploads = new Set()

      const processQueue = () => {
        while (activeUploads.size < MAX_CONCURRENT && queue.length > 0 && task.status === 'uploading' && !paused.value) {
          const chunkIndex = queue.shift()
          const upload = uploadChunkNative(task, chunkIndex)

          const promise = upload.then(() => {
            activeUploads.delete(promise)
            completedChunks++
            task.completedChunks = completedChunks
            task.progress = Math.round((completedChunks / task.totalChunks) * 100)
            processQueue()
          }).catch(error => {
            activeUploads.delete(promise)
            console.error(`Chunk ${chunkIndex} failed:`, error)
            // 失败后重新加入队列，最多重试3次
            if (error.retryCount === undefined) {
              error.retryCount = 1
            } else {
              error.retryCount++
            }

            if (error.retryCount <= MAX_RETRY) {
              queue.unshift(chunkIndex)
            } else {
              task.status = 'error'
              task.error = `分片上传失败: ${error.message}`
              Snackbar.error(`${task.file.name} 上传失败: ${error.message}`)
              reject(error)
            }
            processQueue()
          })

          activeUploads.add(promise)
        }

        // 当所有任务完成时
        if (activeUploads.size === 0 && queue.length === 0) {
          if (task.status === 'uploading') {
            task.progress = 100
            task.status = 'success'
            Snackbar.success(`${task.file.name} 上传成功`)
            emit('upload-complete')
            
            // 检查是否所有任务都已完成
            const allCompleted = uploadTasks.value.every(t => t.status === 'success' || t.status === 'error' || t.status === 'cancelled')
            if (allCompleted) {
              // 延迟关闭弹框，让用户看到上传结果
              setTimeout(() => {
                close()
              }, 1000)
            }
            resolve()
          }
        }
      }

      // 开始处理队列
      processQueue()

    } catch (error) {
      console.error('Upload error:', error)
      task.status = 'error'
      task.error = error.response?.data?.error || error.message
      Snackbar.error(`${task.file.name} 上传失败: ${error.message}`)
      reject(error)
    }
  })
}

// 原生XHR上传分片
const uploadChunkNative = (task, chunkIndex) => {
  return new Promise((resolve, reject) => {
    const file = task.file
    const chunkSize = CHUNK_SIZE
    const start = chunkIndex * chunkSize
    const end = Math.min(start + chunkSize, file.size)
    const chunk = file.slice(start, end)

    const formData = new FormData()
    formData.append('file_id', task.id)
    formData.append('chunk_index', chunkIndex)
    formData.append('chunk_data', chunk)

    const xhr = new XMLHttpRequest()

    // 存储XHR以便可以取消
    const taskKey = `${task.id}_${chunkIndex}`
    uploadTasksMap.value.set(taskKey, xhr)

    // 上传进度
    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        // 更新上传速度
        updateUploadSpeed(e.loaded)
      }
    })

    xhr.onload = () => {
      uploadTasksMap.value.delete(taskKey)
      if (xhr.status === 200) {
        try {
          const response = JSON.parse(xhr.responseText)
          if (response.error) {
            reject(new Error(response.error))
          } else {
            resolve(response)
          }
        } catch (error) {
          reject(new Error('Invalid response format'))
        }
      } else {
        reject(new Error(`HTTP error ${xhr.status}`))
      }
    }

    xhr.onerror = () => {
      uploadTasksMap.value.delete(taskKey)
      reject(new Error('Network error'))
    }

    xhr.ontimeout = () => {
      uploadTasksMap.value.delete(taskKey)
      reject(new Error('Upload timeout'))
    }

    // 设置超时
    xhr.timeout = 30000

    // 发送请求
    xhr.open('POST', '/api/upload/chunk')
    xhr.send(formData)
  })
}

// 开始计算上传速度
const startSpeedCalculation = () => {
  lastUploadedBytes.value = 0
  lastSpeedTime.value = Date.now()
  
  if (speedInterval.value) {
    clearInterval(speedInterval.value)
  }
  
  speedInterval.value = setInterval(() => {
    const currentTime = Date.now()
    const timeElapsed = (currentTime - lastSpeedTime.value) / 1000
    
    if (timeElapsed > 0) {
      const speed = lastUploadedBytes.value / timeElapsed
      uploadSpeed.value = formatSize(speed)
      
      lastUploadedBytes.value = 0
      lastSpeedTime.value = currentTime
    }
  }, 1000)
}

// 停止计算上传速度
const stopSpeedCalculation = () => {
  if (speedInterval.value) {
    clearInterval(speedInterval.value)
    speedInterval.value = null
  }
  uploadSpeed.value = '0 B'
}

// 更新上传速度
const updateUploadSpeed = (bytes) => {
  lastUploadedBytes.value += bytes
}

// 暂停上传
const pauseUpload = () => {
  paused.value = true
}

// 继续上传
const resumeUpload = () => {
  paused.value = false
  // 重新开始处理队列
  for (const task of uploadTasks.value) {
    if (task.status === 'uploading') {
      // 任务会自动继续处理队列
    }
  }
}

const retryUpload = (task) => {
  task.status = 'pending'
  task.progress = 0
  task.uploadedChunks = []
  uploadFile(task)
}

const cancelUpload = async (task) => {
  if (task.abortController) {
    task.abortController.abort()
  }
  
  // 取消所有相关的上传任务
  uploadTasksMap.value.forEach((xhr, key) => {
    if (key.startsWith(task.id)) {
      xhr.abort()
      uploadTasksMap.value.delete(key)
    }
  })
  
  await uploadApi.cancelUpload(task.id)
  task.status = 'cancelled'
  Snackbar.info(`${task.file.name} 已取消上传`)
}

const close = () => {
  visible.value = false
  
  // 取消所有上传任务
  uploadTasksMap.value.forEach((xhr) => {
    xhr.abort()
  })
  uploadTasksMap.value.clear()
  
  // 清空上传任务
  uploadTasks.value = []
  
  // 停止速度计算
  stopSpeedCalculation()
  uploading.value = false
  paused.value = false
  
  emit('update:visible', false)
}

// 暴露方法给父组件
const addFilesFromDrop = (files) => {
  addFiles(files, true)
}

defineExpose({
  addFiles: addFilesFromDrop
})
</script>

<style scoped>
.upload-dialog {
  background-color: #fff;
  border-radius: 16px;
  overflow: hidden;
}

.dark .upload-dialog {
  background-color: #2a2a3a;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.upload-speed {
  font-size: 14px;
  color: #666;
  white-space: nowrap;
}

.upload-controls {
  padding: 12px 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.dark .dialog-header {
  border-bottom-color: #3a3a4a;
}

.dialog-header var-icon {
  cursor: pointer;
}

.upload-area {
  margin: 20px;
  padding: 40px;
  border: 2px dashed #d0d0d0;
  border-radius: 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.dark .upload-area {
  border-color: #4a4a5a;
}

.upload-area:hover {
  border-color: #3f51b5;
  background-color: rgba(63, 81, 181, 0.05);
}

.upload-area.drag-over {
  border-color: #3f51b5;
  background-color: rgba(63, 81, 181, 0.1);
  transform: scale(1.02);
  transition: all 0.2s ease;
}

.upload-area.drag-over var-icon {
  color: #3f51b5;
  transform: scale(1.1);
  transition: all 0.2s ease;
}

.upload-area var-icon {
  margin-bottom: 12px;
  color: #999;
  transition: all 0.2s ease;
}

.upload-area p {
  margin-bottom: 16px;
  color: #999;
  transition: all 0.2s ease;
}

.upload-area .drag-hint {
  color: #3f51b5;
  font-weight: 500;
  font-size: 16px;
}

.upload-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.upload-list {
  max-height: 300px;
  overflow-y: auto;
  padding: 0 20px;
}

.upload-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.dark .upload-item {
  border-bottom-color: #3a3a4a;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.item-info .info {
  flex: 1;
}

.item-info .name {
  font-size: 14px;
  font-weight: 500;
}

.item-info .size {
  font-size: 12px;
  color: #999;
}

.item-progress {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-progress .var-progress {
  flex: 1;
}

.status {
  min-width: 80px;
  font-size: 12px;
}

.status .success {
  color: #4caf50;
}

.status .error {
  color: #f44336;
}

.status .waiting {
  color: #ff9800;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
}

.dark .dialog-footer {
  border-top-color: #3a3a4a;
}
</style>