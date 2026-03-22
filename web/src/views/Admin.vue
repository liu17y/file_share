<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

// 响应式数据
const storageInfo = ref({})
const storagePath = ref('')
const newStoragePath = ref('')
const pathUpdateDialogVisible = ref(false)
const logs = ref([])
const isLoading = ref(false)

// 加载存储信息
const loadStorageInfo = async () => {
  try {
    const response = await fetch('/api/storage')
    storageInfo.value = await response.json()
  } catch (error) {
    console.error('加载存储信息失败:', error)
  }
}

// 更新存储路径
const updateStoragePath = async () => {
  if (!newStoragePath.value.trim()) return
  
  try {
    const formData = new FormData()
    formData.append('new_path', newStoragePath.value)
    
    const response = await fetch('/api/storage/path', {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    if (data.success) {
      pathUpdateDialogVisible.value = false
      newStoragePath.value = ''
      loadStorageInfo()
      alert('存储路径更新成功')
    } else {
      alert('存储路径更新失败')
    }
  } catch (error) {
    console.error('更新存储路径失败:', error)
    alert('更新存储路径失败')
  }
}

// 加载操作日志
const loadLogs = async () => {
  isLoading.value = true
  try {
    // 这里需要根据实际的日志接口来实现
    // 暂时使用模拟数据
    logs.value = [
      { id: 1, time: '2026-03-25 10:00:00', action: '上传文件', user: 'anonymous', details: '上传了文件 example.txt' },
      { id: 2, time: '2026-03-25 09:30:00', action: '创建文件夹', user: 'anonymous', details: '创建了文件夹 documents' },
      { id: 3, time: '2026-03-25 09:00:00', action: '删除文件', user: 'anonymous', details: '删除了文件 old.txt' }
    ]
  } catch (error) {
    console.error('加载日志失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 初始化图表
const initCharts = () => {
  // 存储使用情况图表
  const storageChart = echarts.init(document.getElementById('storageChart'))
  const storageOption = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      top: '5%',
      left: 'center'
    },
    series: [
      {
        name: '存储使用情况',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          {
            value: storageInfo.value.used || 0,
            name: '已使用'
          },
          {
            value: storageInfo.value.free || 0,
            name: '剩余'
          }
        ]
      }
    ]
  }
  storageChart.setOption(storageOption)
  
  // 操作统计图表
  const operationChart = echarts.init(document.getElementById('operationChart'))
  const operationOption = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['1月', '2月', '3月', '4月', '5月', '6月']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '上传',
        type: 'line',
        stack: 'Total',
        data: [120, 132, 101, 134, 90, 230]
      },
      {
        name: '下载',
        type: 'line',
        stack: 'Total',
        data: [220, 182, 191, 234, 290, 330]
      },
      {
        name: '删除',
        type: 'line',
        stack: 'Total',
        data: [150, 232, 201, 154, 190, 330]
      }
    ]
  }
  operationChart.setOption(operationOption)
  
  // 响应式调整
  window.addEventListener('resize', () => {
    storageChart.resize()
    operationChart.resize()
  })
}

// 生命周期钩子
onMounted(() => {
  loadStorageInfo()
  loadLogs()
  // 延迟初始化图表，确保 DOM 元素已渲染
  setTimeout(initCharts, 100)
})
</script>

<template>
  <div class="admin-container">
    <!-- 顶部导航栏 -->
    <div class="header">
      <div class="header-left">
        <h1>AuroraShare · 管理后台</h1>
      </div>
      <div class="header-right">
        <var-button @click="$router.push('/')" type="primary">
          <var-icon name="home" />
          返回主页
        </var-button>
      </div>
    </div>
    
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧导航 -->
      <div class="sidebar">
        <var-menu active="dashboard" class="sidebar-menu">
          <var-menu-item value="dashboard">
            <var-icon name="dashboard" />
            <span>仪表盘</span>
          </var-menu-item>
          <var-menu-item value="logs">
            <var-icon name="document-text" />
            <span>操作日志</span>
          </var-menu-item>
          <var-menu-item value="monitor">
            <var-icon name="monitor" />
            <span>监控</span>
          </var-menu-item>
          <var-menu-item value="analysis">
            <var-icon name="pie-chart" />
            <span>分析</span>
          </var-menu-item>
          <var-menu-item value="storage">
            <var-icon name="hard-drive" />
            <span>存储管理</span>
          </var-menu-item>
        </var-menu>
      </div>
      
      <!-- 右侧内容 -->
      <div class="content">
        <!-- 仪表盘 -->
        <div class="dashboard">
          <h2>仪表盘</h2>
          
          <!-- 统计卡片 -->
          <div class="stats-cards">
            <var-card class="stat-card">
              <div class="stat-item">
                <div class="stat-value">{{ (storageInfo.total / (1024 * 1024 * 1024)).toFixed(2) }} GB</div>
                <div class="stat-label">总存储空间</div>
              </div>
            </var-card>
            <var-card class="stat-card">
              <div class="stat-item">
                <div class="stat-value">{{ (storageInfo.used / (1024 * 1024 * 1024)).toFixed(2) }} GB</div>
                <div class="stat-label">已用空间</div>
              </div>
            </var-card>
            <var-card class="stat-card">
              <div class="stat-item">
                <div class="stat-value">{{ (storageInfo.free / (1024 * 1024 * 1024)).toFixed(2) }} GB</div>
                <div class="stat-label">剩余空间</div>
              </div>
            </var-card>
            <var-card class="stat-card">
              <div class="stat-item">
                <div class="stat-value">{{ storageInfo.percent }}%</div>
                <div class="stat-label">使用率</div>
              </div>
            </var-card>
          </div>
          
          <!-- 图表区域 -->
          <div class="charts-container">
            <var-card class="chart-card">
              <template #header>
                <div class="card-header">
                  <h3>存储使用情况</h3>
                </div>
              </template>
              <div id="storageChart" style="width: 100%; height: 300px;"></div>
            </var-card>
            <var-card class="chart-card">
              <template #header>
                <div class="card-header">
                  <h3>操作统计</h3>
                </div>
              </template>
              <div id="operationChart" style="width: 100%; height: 300px;"></div>
            </var-card>
          </div>
        </div>
        
        <!-- 操作日志 -->
        <div class="logs-section">
          <h2>操作日志</h2>
          <var-card>
            <var-skeleton v-if="isLoading" :rows="5" />
            <div v-else class="logs-table">
              <var-table :data="logs" border>
                <var-table-column prop="id" label="ID" width="80" />
                <var-table-column prop="time" label="时间" width="180" />
                <var-table-column prop="action" label="操作" width="120" />
                <var-table-column prop="user" label="用户" width="120" />
                <var-table-column prop="details" label="详情" />
              </var-table>
              <div v-if="logs.length === 0" class="empty-state">
                <var-icon name="document-text" size="48" color="#c0c4cc" />
                <p>暂无日志记录</p>
              </div>
            </div>
          </var-card>
        </div>
        
        <!-- 存储管理 -->
        <div class="storage-section">
          <h2>存储管理</h2>
          <var-card>
            <div class="storage-info">
              <div class="storage-item">
                <span class="label">当前存储路径:</span>
                <span class="value">{{ storageInfo.base_dir }}</span>
              </div>
              <div class="storage-item">
                <span class="label">总空间:</span>
                <span class="value">{{ (storageInfo.total / (1024 * 1024 * 1024)).toFixed(2) }} GB</span>
              </div>
              <div class="storage-item">
                <span class="label">已用空间:</span>
                <span class="value">{{ (storageInfo.used / (1024 * 1024 * 1024)).toFixed(2) }} GB</span>
              </div>
              <div class="storage-item">
                <span class="label">剩余空间:</span>
                <span class="value">{{ (storageInfo.free / (1024 * 1024 * 1024)).toFixed(2) }} GB</span>
              </div>
              <div class="storage-item">
                <span class="label">使用率:</span>
                <span class="value">{{ storageInfo.percent }}%</span>
              </div>
              <div class="storage-actions">
                <var-button type="primary" @click="pathUpdateDialogVisible = true">
                  <var-icon name="edit" />
                  修改存储路径
                </var-button>
              </div>
            </div>
          </var-card>
        </div>
      </div>
    </div>
    
    <!-- 修改存储路径对话框 -->
    <var-dialog v-model:show="pathUpdateDialogVisible" title="修改存储路径">
      <var-input v-model="newStoragePath" placeholder="请输入新的存储路径" />
      <div class="dialog-tip">
        <var-icon name="info-circle" color="#409eff" />
        <span>请确保新路径存在且具有写入权限</span>
      </div>
      <template #footer>
        <var-button @click="pathUpdateDialogVisible = false">取消</var-button>
        <var-button type="primary" @click="updateStoragePath">确定</var-button>
      </template>
    </var-dialog>
  </div>
</template>

<style scoped>
.admin-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background-color: #ffffff;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.main-content {
  display: flex;
  min-height: calc(100vh - 60px);
}

.sidebar {
  width: 200px;
  background-color: #ffffff;
  border-right: 1px solid #e4e7ed;
}

.sidebar-menu {
  height: 100%;
}

.content {
  flex: 1;
  padding: 20px;
}

.dashboard h2,
.logs-section h2,
.storage-section h2 {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #303133;
}

.stats-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  min-width: 200px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.charts-container {
  display: flex;
  gap: 20px;
}

.chart-card {
  flex: 1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.logs-table {
  margin-top: 10px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.empty-state p {
  margin-top: 10px;
  font-size: 16px;
}

.storage-info {
  padding: 10px 0;
}

.storage-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.storage-item:last-child {
  border-bottom: none;
}

.storage-item .label {
  font-size: 14px;
  color: #606266;
}

.storage-item .value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.storage-actions {
  margin-top: 20px;
  text-align: right;
}

.dialog-tip {
  margin-top: 15px;
  padding: 10px;
  background-color: #ecf5ff;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #409eff;
}

@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e4e7ed;
  }
  
  .stats-cards {
    flex-direction: column;
  }
  
  .charts-container {
    flex-direction: column;
  }
}
</style>