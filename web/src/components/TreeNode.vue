<template>
  <div class="tree-node-item">
    <div
      class="node"
      :class="{ selected: node.path === selectedPath }"
      @click="handleClick"
    >
      <div class="custom-icon">
        <svg v-if="expanded" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
        </svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>
        </svg>
      </div>
      <span class="name">{{ node.name }}</span>
      <var-icon
        v-if="node.children && node.children.length"
        :name="expanded ? 'chevron-down' : 'chevron-right'"
        class="expand-icon"
        @click.stop="toggleExpand"
      />
    </div>
    <div v-if="expanded && node.children && node.children.length" class="children">
      <TreeNode
        v-for="child in node.children"
        :key="child.path"
        :node="child"
        :selected-path="selectedPath"
        @select="$emit('select', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  },
  selectedPath: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['select'])

const expanded = ref(false)

const handleClick = () => {
  emit('select', props.node.path)
}

const toggleExpand = () => {
  expanded.value = !expanded.value
}
</script>

<style scoped>
.tree-node-item {
  user-select: none;
}

.node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px 6px 32px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.node:hover {
  background-color: #f5f5f5;
}

.dark .node:hover {
  background-color: #353545;
}

.node.selected {
  background-color: #e8eaf6;
  color: #3f51b5;
}

.dark .node.selected {
  background-color: #3f51b5;
  color: #fff;
}

.name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.expand-icon {
  font-size: 14px;
  color: #999;
  cursor: pointer;
}

.children {
  margin-left: 16px;
}
</style>