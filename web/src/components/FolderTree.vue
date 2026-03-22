<template>
  <div class="folder-tree">
    <div class="tree-header">
      <var-icon name="folder" />
      <span>文件夹树</span>
      <var-button size="small" text @click="refresh">
        <var-icon name="refresh" />
      </var-button>
    </div>
    <div class="tree-content">
      <div class="tree-node root" :class="{ selected: internalSelectedPath === '' }" @click="selectRoot">
        <div class="custom-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
          </svg>
        </div>
        <span>根目录</span>
      </div>
      <div v-if="loading" class="loading">
        <var-loading type="circle" size="small" />
      </div>
      <div v-else class="tree-nodes">
        <TreeNode
          v-for="node in tree"
          :key="node.path"
          :node="node"
          :selected-path="internalSelectedPath"
          @select="handleSelect"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { fileApi } from '@/api'
import TreeNode from './TreeNode.vue'

const props = defineProps({
  selectedPath: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select'])
const loading = ref(false)
const tree = ref([])
const internalSelectedPath = ref(props.selectedPath)

// 监听外部 selectedPath 变化
watch(() => props.selectedPath, (newPath) => {
  internalSelectedPath.value = newPath
})

const loadTree = async (path = '') => {
  loading.value = true
  try {
    const res = await fileApi.getFolderTree(path)
    tree.value = res.tree || []
  } catch (error) {
    console.error('加载文件夹树失败', error)
  } finally {
    loading.value = false
  }
}

const refresh = () => {
  loadTree()
}

const selectRoot = () => {
  internalSelectedPath.value = ''
  emit('select', '')
}

const handleSelect = (path) => {
  internalSelectedPath.value = path
  emit('select', path)
}

onMounted(() => {
  loadTree()
})

// 暴露方法给父组件
defineExpose({
  refresh
})
</script>

<script>
export default {
  components: { TreeNode }
}
</script>

<style scoped>
.folder-tree {
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.dark .folder-tree {
  background-color: #2a2a3a;
}

.tree-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  font-weight: 500;
}

.dark .tree-header {
  border-bottom-color: #3a3a4a;
}

.tree-header span {
  flex: 1;
}

.tree-content {
  padding: 8px 0;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.tree-node:hover {
  background-color: #f5f5f5;
}

.dark .tree-node:hover {
  background-color: #353545;
}

.tree-node.root {
  font-weight: 500;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 8px;
}

.tree-node.root.selected {
  background-color: #e8eaf6;
  color: #3f51b5;
}

.dark .tree-node.root.selected {
  background-color: #3f51b5;
  color: #fff;
}

.dark .tree-node.root {
  border-bottom-color: #3a3a4a;
}

.loading {
  text-align: center;
  padding: 20px;
}
</style>