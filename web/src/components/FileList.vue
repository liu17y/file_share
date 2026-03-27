<template>
  <div class="file-list">
    <div class="list-header">
      <div class="select-all">
        <var-checkbox
          :checked="isAllSelected"
          @change="toggleSelectAll"
        />
      </div>
      <div class="name">名称</div>
      <div class="size">大小</div>
      <div class="modified">修改时间</div>
      <div class="actions">操作</div>
    </div>

    <div v-if="loading" class="loading">
      <div v-for="i in 5" :key="i" class="skeleton-item">
        <var-skeleton :loading="loading" animated>
          <div class="skeleton-content">
            <div class="skeleton-icon"></div>
            <div class="skeleton-text"></div>
            <div class="skeleton-meta"></div>
          </div>
        </var-skeleton>
      </div>
    </div>

    <div v-else-if="files.length === 0" class="empty">
      <var-icon name="folder-open" :size="64" />
      <p>暂无文件</p>
    </div>

    <div v-else class="list-body">
      <div
        v-for="file in files"
        :key="file.path"
        class="file-item"
        :class="{ selected: isSelected(file), dragging: isDragging && draggedFile?.path === file.path, 'drag-over': dragOverFile?.path === file.path }"
        draggable="true"
        @dragstart="handleDragStart(file, $event)"
        @dragover="handleDragOver(file, $event)"
        @dragleave="handleDragLeave"
        @drop="handleDrop(file, $event)"
        @dragend="handleDragEnd"
      >
        <div class="select-col">
          <var-checkbox
            :checked="isSelected(file)"
            @change="toggleSelect(file)"
          />
        </div>

        <div class="name-col" @click="handleClick(file)">
          <div v-if="file.is_dir" class="custom-icon folder-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" color="#ff9800">
              <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
            </svg>
          </div>
          <div v-else class="custom-icon file-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" color="#3f51b5">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="tooltip-container">
            <var-tooltip :content="file.name" placement="top">
              <span class="filename" :class="{ 'folder-name': file.is_dir }">{{ truncateFilename(file.name, file.is_dir) }}</span>
            </var-tooltip>
          </div>
        </div>

        <div class="size-col">
          {{ file.is_dir ? '-' : formatSize(file.size) }}
        </div>

        <div class="modified-col">
          {{ formatDate(file.modified) }}
        </div>

        <div class="actions-col">
          <var-button
            v-if="!file.is_dir"
            size="small"
            text
            @click.stop="$emit('preview', file)"
          >
            <var-icon name="eye" />
          </var-button>
          <var-button
            v-if="!file.is_dir"
            size="small"
            text
            @click.stop="$emit('download', file)"
          >
            <var-icon name="download" />
          </var-button>
          <var-button
            size="small"
            text
            class="rename-button"
            @click.stop="$emit('rename', file)"
          >
            <var-icon name="edit" />
            <span>重命名</span>
          </var-button>
          <var-button
            size="small"
            text
            @click.stop="$emit('delete', file)"
          >
            <var-icon name="delete" />
          </var-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  files: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  selected: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['select', 'preview', 'download', 'rename', 'delete', 'folder-click', 'move'])

const isDragging = ref(false)
const draggedFile = ref(null)
const dragOverFile = ref(null)

const isSelected = (file) => {
  return props.selected.some(s => s.path === file.path)
}

const isAllSelected = computed(() => {
  return props.files.length > 0 && props.selected.length === props.files.length
})

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    // 取消全选
    emit('select', null)
  } else {
    // 全选所有文件 - 发送特殊事件
    emit('select', { type: 'select-all', files: props.files })
  }
}

const toggleSelect = (file) => {
  emit('select', file)
}

const handleClick = (file) => {
  if (file.is_dir) {
    emit('folder-click', file)
  } else {
    emit('preview', file)
  }
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const truncateFilename = (filename, isDir = false, maxLength = 30) => {
  if (filename.length <= maxLength) {
    return filename
  }

  // 目录名称直接截断，不需要考虑扩展名
  if (isDir) {
    return filename.substring(0, maxLength - 3) + '...'
  }

  // 文件名称保留扩展名
  const extension = filename.lastIndexOf('.') > -1 ? filename.substring(filename.lastIndexOf('.')) : ''
  const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.'))
  const availableLength = maxLength - extension.length - 3 // 3 for ellipsis
  return nameWithoutExt.substring(0, availableLength) + '...' + extension
}

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    pdf: 'file-pdf',
    jpg: 'file-image',
    jpeg: 'file-image',
    png: 'file-image',
    gif: 'file-image',
    mp4: 'file-video',
    mp3: 'file-music',
    zip: 'file-zip',
    rar: 'file-zip',
    txt: 'file-text',
    doc: 'file-word',
    docx: 'file-word',
    xls: 'file-excel',
    xlsx: 'file-excel'
  }
  return iconMap[ext] || 'file'
}

const handleDragStart = (file, event) => {
  isDragging.value = true
  draggedFile.value = file
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', file.path)
}

const handleDragOver = (file, event) => {
  if (!draggedFile.value || draggedFile.value.path === file.path) {
    return
  }
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  dragOverFile.value = file
}

const handleDragLeave = () => {
  dragOverFile.value = null
}

const handleDrop = (targetFile, event) => {
  event.preventDefault()
  dragOverFile.value = null

  if (!draggedFile.value || draggedFile.value.path === targetFile.path) {
    return
  }

  if (!targetFile.is_dir) {
    return
  }

  emit('move', {
    sources: [draggedFile.value.path],
    destination: targetFile.path
  })

  isDragging.value = false
  draggedFile.value = null
}

const handleDragEnd = () => {
  isDragging.value = false
  draggedFile.value = null
  dragOverFile.value = null
}
</script>

<style scoped>
.file-list {
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.dark .file-list {
  background-color: #2a2a3a;
}

.list-header {
  display: flex;
  padding: 12px 16px;
  background-color: #fafafa;
  border-bottom: 1px solid #e0e0e0;
  font-size: 14px;
  font-weight: 500;
  color: #666;
}

.dark .list-header {
  background-color: #1e1e2a;
  border-bottom-color: #3a3a4a;
  color: #aaa;
}

.select-all {
  width: 40px;
}

.name {
  flex: 1;
}

.size {
  width: 100px;
}

.modified {
  width: 160px;
}

.actions {
  width: 120px;
  text-align: right;
}

.list-body {
  max-height: calc(100vh - 300px);
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
  cursor: default;
}

.dark .file-item {
  border-bottom-color: #3a3a4a;
}

.file-item:hover {
  background-color: #f5f5f5;
}

.dark .file-item:hover {
  background-color: #353545;
}

.file-item.selected {
  background-color: #e8eaf6;
}

.dark .file-item.selected {
  background-color: #3f51b5;
}

.file-item.dragging {
  opacity: 0.5;
}

.file-item.drag-over {
  background-color: #c8e6c9;
}

.dark .file-item.drag-over {
  background-color: #2e7d32;
}

.select-col {
  width: 40px;
}

.name-col {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  min-width: 0;
  max-width: 100%;
}

.tooltip-container {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.custom-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.folder-icon {
  filter: drop-shadow(0 2px 4px rgba(255, 152, 0, 0.3));
  transition: all 0.2s ease;
}

.file-icon {
  filter: drop-shadow(0 2px 4px rgba(63, 81, 181, 0.3));
  transition: all 0.2s ease;
}

.folder-icon:hover {
  transform: scale(1.1);
  filter: drop-shadow(0 3px 6px rgba(255, 152, 0, 0.4));
}

.name-col:hover .file-icon {
  transform: scale(1.05);
  filter: drop-shadow(0 2px 4px rgba(63, 81, 181, 0.3));
}

.folder-name {
  font-weight: 600;
  color: #333;
}

.filename {
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.dark .filename {
  color: #eee;
}

.size-col {
  width: 100px;
  color: #999;
  font-size: 13px;
}

.modified-col {
  width: 160px;
  color: #999;
  font-size: 13px;
}

.actions-col {
  width: 180px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.rename-button {
  color: #4caf50;
  font-weight: 500;
}

.rename-button:hover {
  background-color: rgba(76, 175, 80, 0.1);
}

.loading {
  padding: 20px 16px;
}

.skeleton-item {
  margin-bottom: 12px;
}

.skeleton-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
}

.skeleton-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background-color: #e0e0e0;
}

.dark .skeleton-icon {
  background-color: #4a4a4a;
}

.skeleton-text {
  flex: 1;
  height: 16px;
  border-radius: 4px;
  background-color: #e0e0e0;
}

.dark .skeleton-text {
  background-color: #4a4a4a;
}

.skeleton-meta {
  width: 260px;
  height: 14px;
  border-radius: 4px;
  background-color: #e0e0e0;
}

.dark .skeleton-meta {
  background-color: #4a4a4a;
}

.empty {
  text-align: center;
  padding: 60px;
  color: #999;
}

.empty .var-icon {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .modified-col {
    display: none;
  }

  .size-col {
    width: 80px;
  }

  .actions-col {
    width: 100px;
  }
}
</style>