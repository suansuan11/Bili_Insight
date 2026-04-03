<template>
  <div class="analysis-view">
    <!-- Top Stats Row -->
    <div class="stats-row">
      <div class="stat-card stat-total">
        <div class="stat-icon">
          <el-icon :size="28"><DataAnalysis /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-number">{{ taskStats.total }}</span>
          <span class="stat-label">Total Tasks</span>
        </div>
      </div>
      <div class="stat-card stat-completed">
        <div class="stat-icon">
          <el-icon :size="28"><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-number">{{ taskStats.completed }}</span>
          <span class="stat-label">Completed</span>
        </div>
      </div>
      <div class="stat-card stat-running">
        <div class="stat-icon">
          <el-icon :size="28"><Loading /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-number">{{ taskStats.running }}</span>
          <span class="stat-label">Running</span>
        </div>
      </div>
      <div class="stat-card stat-failed">
        <div class="stat-icon">
          <el-icon :size="28"><CircleClose /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-number">{{ taskStats.failed }}</span>
          <span class="stat-label">Failed</span>
        </div>
      </div>
    </div>

    <!-- Submit Section -->
    <div class="submit-section">
      <div class="submit-header">
        <h2 class="submit-title">提交视频分析</h2>
        <p class="submit-subtitle">输入B站视频的 BVID，系统将自动爬取弹幕与评论并进行情感分析</p>
      </div>
      <div class="submit-form">
        <el-input
          v-model="bvid"
          placeholder="请输入视频 BVID"
          class="bvid-input"
          size="large"
          :disabled="isSubmitting"
          @keyup.enter="handleAnalyze"
          clearable
        >
          <template #prefix>
            <el-icon><VideoPlay /></el-icon>
          </template>
          <template #prepend>BV</template>
        </el-input>
        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          @click="handleAnalyze"
          :loading="isSubmitting"
          :icon="DataAnalysis"
        >
          开始分析
        </el-button>
      </div>
      <p class="submit-helper">示例: BV1xx411c7mC</p>
    </div>

    <!-- Task List Section -->
    <div class="task-list-section">
      <div class="task-list-header">
        <h2 class="task-list-title">
          分析任务列表
          <el-tag type="info" size="small" round class="task-count-tag">{{ filteredTasks.length }}</el-tag>
        </h2>
        <el-radio-group v-model="statusFilter" size="default">
          <el-radio-button value="ALL">全部</el-radio-button>
          <el-radio-button value="RUNNING">进行中</el-radio-button>
          <el-radio-button value="COMPLETED">已完成</el-radio-button>
          <el-radio-button value="FAILED">失败</el-radio-button>
        </el-radio-group>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <el-icon class="is-loading" :size="36"><Loading /></el-icon>
        <p>正在加载任务列表...</p>
      </div>

      <!-- Empty State -->
      <el-empty
        v-else-if="filteredTasks.length === 0"
        :description="statusFilter === 'ALL' ? '暂无分析任务，提交一个视频开始吧' : '没有匹配的任务'"
        :image-size="160"
      />

      <!-- Task Grid -->
      <div v-else class="task-grid">
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          class="task-card"
          :class="{ 'task-card--clickable': task.status === 'COMPLETED' }"
          @click="handleTaskClick(task)"
        >
          <div class="task-card-top">
            <div class="task-title-group">
              <span class="task-title">{{ task.title || task.bvid }}</span>
              <span v-if="task.title" class="task-bvid">{{ task.bvid }}</span>
            </div>
            <el-tag
              :type="getStatusType(task.status)"
              size="small"
              effect="dark"
              round
            >
              {{ getStatusText(task.status) }}
            </el-tag>
          </div>

          <div v-if="task.status === 'RUNNING' || task.status === 'PENDING'" class="task-progress-section">
            <div class="task-step">
              <el-icon class="is-loading" :size="12"><Loading /></el-icon>
              <span>{{ task.currentStep || (task.status === 'PENDING' ? '等待处理中...' : '正在处理中...') }}</span>
            </div>
            <el-progress
              :percentage="task.progress || 0"
              :stroke-width="6"
              :color="'#409eff'"
              :striped="true"
              :striped-flow="true"
              :duration="10"
              class="task-progress"
            />
          </div>

          <div class="task-card-footer">
            <span class="task-time">
              <el-icon :size="12"><Clock /></el-icon>
              {{ formatDate(task.createdAt) }}
            </span>
            <el-icon v-if="task.status === 'COMPLETED'" :size="14" class="task-arrow"><Right /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  VideoPlay,
  Loading,
  DataAnalysis,
  CircleCheck,
  CircleClose,
  Clock,
  Right
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { submitAnalysis, getRecentTasks, getTaskStatus } from '@/api/analysis'
import type { AnalysisTask } from '@/types/analysis'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const bvid = ref('')
const tasks = ref<AnalysisTask[]>([])
const isSubmitting = ref(false)
const isLoading = ref(false)
const statusFilter = ref<string>('ALL')

let pollTimer: ReturnType<typeof setInterval> | null = null

// Computed stats from tasks
const taskStats = computed(() => {
  const all = tasks.value
  return {
    total: all.length,
    completed: all.filter(t => t.status === 'COMPLETED').length,
    running: all.filter(t => t.status === 'RUNNING' || t.status === 'PENDING').length,
    failed: all.filter(t => t.status === 'FAILED').length
  }
})

// Filtered tasks based on status filter
const filteredTasks = computed(() => {
  if (statusFilter.value === 'ALL') return tasks.value
  return tasks.value.filter(t => t.status === statusFilter.value)
})

const fetchTasks = async () => {
  isLoading.value = true
  try {
    const response = await getRecentTasks(20)
    if (response.code === 0) {
      tasks.value = response.data
    } else {
      ElMessage.error(response.message || '加载任务列表失败')
    }
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    isLoading.value = false
  }
}

const handleAnalyze = async () => {
  const trimmed = bvid.value.trim()
  if (!trimmed) {
    ElMessage.warning('请输入 BVID')
    return
  }

  // The input prepends "BV" visually, so allow user to type with or without BV prefix
  const finalBvid = trimmed.startsWith('BV') ? trimmed : `BV${trimmed}`

  if (!/^BV[a-zA-Z0-9]{10}$/.test(finalBvid)) {
    ElMessage.warning('BVID 格式不正确，应为 "BV" 开头加10位字符')
    return
  }

  isSubmitting.value = true
  try {
    const response = await submitAnalysis(finalBvid)
    if (response.code === 0) {
      ElMessage.success('分析任务已提交！')
      bvid.value = ''
      await fetchTasks()
      startPolling()
    } else {
      ElMessage.error(response.message || '提交分析失败')
    }
  } catch (error: any) {
    console.error('Failed to submit analysis:', error)
    ElMessage.error(error.message || '提交分析失败')
  } finally {
    isSubmitting.value = false
  }
}

const handleTaskClick = (task: AnalysisTask) => {
  if (task.status === 'COMPLETED') {
    router.push(`/analysis/${task.id}`)
  } else if (task.status === 'FAILED') {
    ElMessage.error(task.errorMessage || '任务执行失败')
  } else {
    ElMessage.info('任务正在处理中，请稍候...')
  }
}

const startPolling = () => {
  if (pollTimer) return
  let failCount = 0

  const poll = async () => {
    const runningTasks = tasks.value.filter(
      t => t.status === 'RUNNING' || t.status === 'PENDING'
    )
    if (runningTasks.length === 0) {
      stopPolling()
      return
    }
    for (const task of runningTasks) {
      try {
        const response = await getTaskStatus(task.id)
        if (response.code === 0 && response.data) {
          const idx = tasks.value.findIndex(t => t.id === task.id)
          if (idx !== -1) {
            Object.assign(tasks.value[idx], response.data)
          }
          failCount = 0
        }
      } catch {
        failCount++
        if (failCount >= 5) stopPolling()
      }
    }
  }

  poll()
  pollTimer = setInterval(poll, 3000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    PENDING: 'info',
    RUNNING: '',
    COMPLETED: 'success',
    FAILED: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    PENDING: '等待中',
    RUNNING: '进行中',
    COMPLETED: '已完成',
    FAILED: '失败'
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
    minute: '2-digit'
  })
}

onMounted(() => {
  fetchTasks().then(() => {
    // Start polling if there are running tasks
    const hasRunning = tasks.value.some(
      t => t.status === 'RUNNING' || t.status === 'PENDING'
    )
    if (hasRunning) startPolling()
  })
  if (route.query.bvid) {
    bvid.value = route.query.bvid.toString()
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.analysis-view {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ===== Stats Row ===== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}

.stat-total::after    { content: ''; position: absolute; right: 0; top: 15%; bottom: 15%; width: 3px; border-radius: 2px; background: #2563eb; }
.stat-completed::after { content: ''; position: absolute; right: 0; top: 15%; bottom: 15%; width: 3px; border-radius: 2px; background: #16a34a; }
.stat-running::after   { content: ''; position: absolute; right: 0; top: 15%; bottom: 15%; width: 3px; border-radius: 2px; background: #d97706; }
.stat-failed::after    { content: ''; position: absolute; right: 0; top: 15%; bottom: 15%; width: 3px; border-radius: 2px; background: #dc2626; }

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 11px;
  flex-shrink: 0;
}

.stat-total    .stat-icon { background: #eff6ff; color: #2563eb; }
.stat-completed .stat-icon { background: #f0fdf4; color: #16a34a; }
.stat-running  .stat-icon { background: #fffbeb; color: #d97706; }
.stat-failed   .stat-icon { background: #fef2f2; color: #dc2626; }

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
  color: #0f172a;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  margin-top: 3px;
}

/* ===== Submit Section ===== */
.submit-section {
  background: #fff;
  border-radius: 12px;
  padding: 28px 32px;
  border: 1px solid #e2e8f0;
}

.submit-header {
  margin-bottom: 20px;
}

.submit-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 6px 0;
}

.submit-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.submit-form {
  display: flex;
  gap: 12px;
  align-items: stretch;
}

.bvid-input {
  flex: 1;
}

.submit-btn {
  min-width: 130px;
  border-radius: 8px;
  font-weight: 600;
}

.submit-helper {
  margin: 10px 0 0 0;
  font-size: 12px;
  color: #9ca3af;
}

/* ===== Task List Section ===== */
.task-list-section {
  background: #fff;
  border-radius: 12px;
  padding: 28px 32px;
  border: 1px solid #e2e8f0;
}

.task-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.task-list-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-count-tag {
  font-size: 12px;
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 0;
  color: #9ca3af;
  gap: 12px;
}

.loading-state p {
  margin: 0;
  font-size: 14px;
}

.is-loading {
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===== Task Grid ===== */
.task-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.task-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: box-shadow 0.25s ease, transform 0.2s ease;
  background: #fafbfc;
}

.task-card:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.task-card--clickable {
  cursor: pointer;
}

.task-card--clickable:hover {
  border-color: #2563eb;
}

.task-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.task-title-group {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.task-title {
  font-size: 15px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-bvid {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
}

.task-progress {
  margin: 2px 0;
}

.task-step {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6b7280;
}

.task-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.task-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #9ca3af;
}

.task-arrow {
  color: #2563eb;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .task-grid {
    grid-template-columns: 1fr;
  }

  .submit-form {
    flex-direction: column;
  }

  .submit-btn {
    min-width: unset;
  }

  .task-list-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
