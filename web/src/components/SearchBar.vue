<template>
  <div class="search-bar">
    <var-input
      v-model="keyword"
      placeholder="搜索文件或文件夹..."
      clearable
      @clear="handleClear"
      @keyup.enter="handleSearch"
    >
      <template #append-icon>
        <var-icon name="search" @click="handleSearch" />
      </template>
    </var-input>
    <div v-if="searching" class="search-tip">
      正在搜索: "{{ keyword }}"
      <var-button size="small" text @click="handleClear">
        <var-icon name="close" />
      </var-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const emit = defineEmits(['search', 'clear'])

const keyword = ref('')
const searching = ref(false)

let searchTimer = null

const handleSearch = () => {
  if (keyword.value.trim()) {
    searching.value = true
    emit('search', keyword.value.trim())
  } else {
    handleClear()
  }
}

const handleClear = () => {
  keyword.value = ''
  searching.value = false
  emit('clear')
}

watch(keyword, (val) => {
  if (searchTimer) clearTimeout(searchTimer)

  if (val.trim()) {
    searchTimer = setTimeout(() => {
      handleSearch()
    }, 300)
  } else {
    handleClear()
  }
})
</script>

<style scoped>
.search-bar {
  padding: 16px 24px;
  background-color: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.dark .search-bar {
  background-color: #2a2a3a;
  border-bottom-color: #3a3a4a;
}

.search-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #3f51b5;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>