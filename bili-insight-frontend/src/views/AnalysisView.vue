<template>
  <div class="analysis-view">
    <el-row :gutter="16" class="mb-6">
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card">
          <div class="metric-title">任务总数</div>
          <div class="metric-value">{{ summary.total }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card success">
          <div class="metric-title">已完成</div>
          <div class="metric-value">{{ summary.completed }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card warning">
          <div class="metric-title">处理中</div>
          <div class="metric-value">{{ summary.processing }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="metric-card danger">
          <div class="metric-title">失败任务</div>
          <div class="metric-value">{{ summary.failed }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="mb-6 border-none" shadow="hover">
      <template #header>
        <div class="font-bold text-lg">新建分析任务</div>
      </template>
      <div class="flex gap-4">
        <el-input
          v-model="bvid"
          placeholder="输入 BVID（如 BV1xx411c7Xj）"
          class="flex-1"
          size="large"
          :disabled="isSubmitting"
        >
          <template #prefix>
            <el-icon><VideoPlay /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" size="large" @click="handleAnalyze" :loading="isSubmitting">
          开始分析
        </el-button>
      </div>
    </el-card>

    <el-card class="mb-4" shadow="never">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="按 BVID 搜索" clearable class="filter-input" />
        <el-radio-group v-model="statusFilter" size="small">
          <el-radio-button label="ALL">全部</el-radio-button>
          <el-radio-button label="PENDING">待处理</el-radio-button>
          <el-radio-button label="PROCESSING">处理中</el-radio-button>
          <el-radio-button label="COMPLETED">已完成</el-radio-button>
          <el-radio-button label="FAILED">失败</el-radio-button>
        </el-radio-group>
        <el-switch v-model="autoRefresh" active-text="自动刷新" />
        <el-button @click="fetchTasks" :loading="isLoading">手动刷新</el-button>
      </div>
    </el-card>

    <div class="task-list">
      <h3 class="text-xl font-bold mb-4">任务列表（{{ filteredTasks.length }}）</h3>

      <div v-if="isLoading" class="text-center py-8">
        <el-icon class="is-loading" size="32"><Loading /></el-icon>
        <p class="mt-2 text-gray-500">正在加载任务...</p>
      </div>

      <el-empty v-else-if="filteredTasks.length === 0" description="暂无匹配任务" />

      <div v-else class="space-y-3">
        <el-card
          v-for="task in filteredTasks"
          :key="task.id"
          class="task-card hover:shadow-md transition-shadow cursor-pointer"
          @click="handleTaskClick(task)"
        >
          <div class="flex justify-between items-center">
            <div class="flex-1">
              <div class="font-bold text-base mb-1">{{ task.bvid }}</div>
              <div class="text-sm text-gray-500">创建时间：{{ formatDate(task.createdAt) }}</div>
              <div v-if="task.currentStep" class="text-xs text-gray-400 mt-1">{{ task.currentStep }}</div>
              <el-progress
                v-if="task.status === 'PROCESSING' || task.status === 'PENDING'"
                :percentage="task.progress || 0"
                :stroke-width="8"
                class="mt-2"
              />
            </div>
            <div class="flex items-center gap-3">
              <el-tag :type="getStatusType(task.status)" size="large">
                {{ getStatusText(task.status) }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { VideoPlay, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { submitAnalysis, getRecentTasks } from '@/api/analysis'
import type { AnalysisTask } from '@/types/analysis'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const bvid = ref('')
const tasks = ref<AnalysisTask[]>([])
const isSubmitting = ref(false)
const isLoading = ref(false)
const keyword = ref('')
const statusFilter = ref('ALL')
const autoRefresh = ref(true)
let refreshTimer: number | null = null

const summary = computed(() => ({
  total: tasks.value.length,
  completed: tasks.value.filter((t) => t.status === 'COMPLETED').length,
  processing: tasks.value.filter((t) => t.status === 'PROCESSING' || t.status === 'PENDING').length,
  failed: tasks.value.filter((t) => t.status === 'FAILED').length,
}))

const filteredTasks = computed(() => {
  return tasks.value.filter((task) => {
    const byKeyword = !keyword.value || task.bvid?.toLowerCase().includes(keyword.value.toLowerCase())
    const byStatus = statusFilter.value === 'ALL' || task.status === statusFilter.value
    return byKeyword && byStatus
  })
})

const fetchTasks = async () => {
  isLoading.value = true
  try {
    const response = await getRecentTasks(50)
    if (response.code === 0) {
      tasks.value = response.data
    } else {
      ElMessage.error(response.message || '加载任务失败')
    }
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
    ElMessage.error('加载任务失败')
  } finally {
    isLoading.value = false
  }
}

const handleAnalyze = async () => {
  if (!bvid.value.trim()) {
    ElMessage.warning('请输入 BVID')
    return
  }

  if (!bvid.value.startsWith('BV')) {
    ElMessage.warning('BVID 应以 BV 开头')
    return
  }

  isSubmitting.value = true
  try {
    const response = await submitAnalysis(bvid.value.trim())
    if (response.code === 0) {
      ElMessage.success('分析任务提交成功')
      bvid.value = ''
      await fetchTasks()
    } else {
      ElMessage.error(response.message || '提交分析任务失败')
    }
  } catch (error: any) {
    console.error('Failed to submit analysis:', error)
    ElMessage.error(error.message || '提交分析任务失败')
  } finally {
    isSubmitting.value = false
  }
}

const handleTaskClick = (task: AnalysisTask) => {
  if (task.status === 'COMPLETED') {
    router.push(`/analysis/${task.id}`)
  } else if (task.status === 'FAILED') {
    ElMessage.warning('该任务执行失败，请重新提交')
  } else {
    ElMessage.info(`任务${getStatusText(task.status)}，请稍后查看`)
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    PENDING: 'info',
    PROCESSING: 'warning',
    COMPLETED: 'success',
    FAILED: 'danger',
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    PENDING: '待处理',
    PROCESSING: '处理中',
    COMPLETED: '已完成',
    FAILED: '失败',
  }
  return texts[status] || status
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const startAutoRefresh = () => {
  if (refreshTimer) window.clearInterval(refreshTimer)
  refreshTimer = window.setInterval(() => {
    if (autoRefresh.value) {
      fetchTasks()
    }
  }, 8000)
}

onMounted(() => {
  fetchTasks()
  startAutoRefresh()
  if (route.query.bvid) {
    bvid.value = route.query.bvid.toString()
  }
})

onBeforeUnmount(() => {
  if (refreshTimer) window.clearInterval(refreshTimer)
})
</script>

<style scoped>
.mb-6 { margin-bottom: 1.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mb-1 { margin-bottom: 0.25rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.gap-4 { gap: 1rem; }
.gap-3 { gap: 0.75rem; }
.flex { display: flex; }
.flex-1 { flex: 1; }
.space-y-3 > * + * { margin-top: 0.75rem; }
.py-8 { padding-top: 2rem; padding-bottom: 2rem; }

.task-card { border-radius: var(--radius-lg); }
.metric-card { border-left: 4px solid #4f46e5; }
.metric-card.success { border-left-color: #10b981; }
.metric-card.warning { border-left-color: #f59e0b; }
.metric-card.danger { border-left-color: #ef4444; }
.metric-title { color: #6b7280; font-size: 13px; }
.metric-value { font-size: 30px; font-weight: 700; color: #111827; margin-top: 6px; }
.toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.filter-input { width: 240px; }

.is-loading { animation: rotating 2s linear infinite; }
@keyframes rotating {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
