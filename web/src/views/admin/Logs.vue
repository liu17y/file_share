<template>
  <div class="logs-page">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <var-input
        v-model="filters.keyword"
        placeholder="搜索操作内容"
        clearable
        @clear="loadLogs"
        @keyup.enter="loadLogs"
      >
        <template #append-icon>
          <var-icon name="search" @click="loadLogs" />
        </template>
      </var-input>

      <var-select
        v-model="filters.level"
        placeholder="日志级别"
        :options="levelOptions"
        clearable
        @change="loadLogs"
      />

      <var-button type="primary" @click="loadLogs">
        <var-icon name="search" /> 查询
      </var-button>
      <var-button @click="resetFilters">
        <var-icon name="refresh" /> 重置
      </var-button>
    </div>

    <!-- 日志表格 -->
    <var-table :data="logs" :loading="loading" class="log-table">
      <var-table-column title="时间" key="time" width="180">
        <template #cell="{ row }">
          {{ formatTime(row.time) }}
        </template>
      </var-table-column>

      <var-table-column title="级别" key="level" width="100">
        <template #cell="{ row }">
          <var-tag :type="getLevelType(row.level)" size="small">
            {{ row.level }}
          </var-tag>
        </template>
      </var-table-column>

      <var-table-column title="操作内容" key="content" min-width="300">
        <template #cell="{ row }">
          {{ row.content }}
        </template>
      </var-table-column>
    </var-table>

    <!-- 分页 -->
    <div class="pagination">
      <var-pagination
        v-model:current="pagination.page"
        :total="pagination.total"
        :page-size="pagination.pageSize"
        @change="loadLogs"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { systemApi } from '@/api'
import { Snackbar } from '@varlet/ui'

const loading = ref(false)
const logs = ref([])

const filters = reactive({
  keyword: '',
  level: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const levelOptions = [
  { label: 'INFO', value: 'INFO' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'DEBUG', value: 'DEBUG' }
]

const getLevelType = (level) => {
  const types = {
    INFO: 'info',
    WARNING: 'warning',
    ERROR: 'danger',
    DEBUG: 'primary'
  }
  return types[level] || 'default'
}

const formatTime = (time) => {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword,
      level: filters.level
    }
    const res = await systemApi.getLogs(params)
    logs.value = res.logs || []
    pagination.total = res.total || 0
  } catch (error) {
    Snackbar.error('加载日志失败')
    // 使用模拟数据
    logs.value = generateMockLogs()
    pagination.total = 100
  } finally {
    loading.value = false
  }
}

const generateMockLogs = () => {
  const mockLogs = []
  const levels = ['INFO', 'INFO', 'INFO', 'WARNING', 'ERROR']
  const actions = ['上传文件', '下载文件', '删除文件', '创建文件夹', '重命名文件', '登录系统', '修改设置']

  for (let i = 0; i < 20; i++) {
    const date = new Date()
    date.setHours(date.getHours() - i)
    mockLogs.push({
      time: date.toISOString(),
      level: levels[Math.floor(Math.random() * levels.length)],
      content: `${actions[Math.floor(Math.random() * actions.length)]} - 操作ID: ${Date.now() + i}`
    })
  }
  return mockLogs
}

const resetFilters = () => {
  filters.keyword = ''
  filters.level = ''
  pagination.page = 1
  loadLogs()
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.logs-page {
  animation: fadeIn 0.3s ease;
}

.filter-bar {
  background-color: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-bar .var-input {
  width: 250px;
}

.filter-bar .var-select {
  width: 150px;
}

.log-table {
  background-color: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-bar .var-input,
  .filter-bar .var-select {
    width: 100%;
  }
}
</style>