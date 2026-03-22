<template>
  <div class="breadcrumb">
    <div class="crumb-item" @click="navigate('')">
      <var-icon name="home" />
      <span>根目录</span>
    </div>
    <var-icon name="chevron-right" class="separator" />
    <div
      v-for="(part, index) in parts"
      :key="index"
      class="crumb-item"
      :class="{ active: index === parts.length - 1 }"
      @click="navigate(parts.slice(0, index + 1).join('/'))"
    >
      <span>{{ part }}</span>
      <var-icon v-if="index < parts.length - 1" name="chevron-right" class="separator" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  path: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['navigate'])

const parts = computed(() => {
  if (!props.path) return []
  return props.path.split('/').filter(p => p)
})

const navigate = (path) => {
  emit('navigate', path)
}
</script>

<style scoped>
.breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  padding: 12px 0;
  margin-bottom: 16px;
}

.crumb-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  transition: color 0.2s;
}

.crumb-item:hover {
  color: #3f51b5;
}

.crumb-item.active {
  color: #333;
  font-weight: 500;
  cursor: default;
}

.dark .crumb-item {
  color: #aaa;
}

.dark .crumb-item.active {
  color: #fff;
}

.separator {
  font-size: 14px;
  color: #ccc;
  margin: 0 4px;
}
</style>