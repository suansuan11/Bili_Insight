<template>
  <div class="analysis-view">
    <el-card class="mb-6 border-none" shadow="hover">
      <template #header>
        <div class="font-bold text-lg">New Analysis Task</div>
      </template>
      <div class="flex gap-4">
        <el-input 
          v-model="bvid" 
          placeholder="Enter Video BVID (e.g., BV1xx411c7Xj)" 
          class="flex-1"
          size="large"
          :disabled="isSubmitting"
        >
          <template #prefix>
            <el-icon><VideoPlay /></el-icon>
          </template>
        </el-input>
        <el-button 
          type="primary" 
          size="large" 
          @click="handleAnalyze"
          :loading="isSubmitting"
        >
          Start Analysis
        </el-button>
      </div>
    </el-card>

    <div class="task-list">
      <h3 class="text-xl font-bold mb-4">Recent Tasks</h3>
      
      <div v-if="isLoading" class="text-center py-8">
        <el-icon class="is-loading" size="32"><Loading /></el-icon>
        <p class="mt-2 text-gray-500">Loading tasks...</p>
      </div>

      <el-empty v-else-if="tasks.length === 0" description="No tasks yet" />
      
      <div v-else class="space-y-3">
        <el-card 
          v-for="task in tasks" 
          :key="task.id"
          class="task-card hover:shadow-md transition-shadow cursor-pointer"
          @click="handleTaskClick(task)"
        >
          <div class="flex justify-between items-center">
            <div class="flex-1">
              <div class="font-bold text-base mb-1">{{ task.bvid }}</div>
              <div class="text-sm text-gray-500">
                Created: {{ formatDate(task.createdAt) }}
              </div>
              <div v-if="task.currentStep" class="text-xs text-gray-400 mt-1">
                {{ task.currentStep }}
              </div>
            </div>
            <div class="flex items-center gap-3">
              <el-progress 
                v-if="task.status === 'PROCESSING'"
                type="circle" 
                :percentage="task.progress || 0" 
                :width="50"
              />
              <el-tag 
                :type="getStatusType(task.status)"
                size="large"
              >
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
import { ref, onMounted } from 'vue'
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

const fetchTasks = async () => {
  isLoading.value = true
  try {
    const response = await getRecentTasks(20)
    if (response.code === 0) {
      tasks.value = response.data
    } else {
      ElMessage.error(response.message || 'Failed to load tasks')
    }
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
    ElMessage.error('Failed to load tasks')
  } finally {
    isLoading.value = false
  }
}

const handleAnalyze = async () => {
  if (!bvid.value.trim()) {
    ElMessage.warning('Please enter a BVID')
    return
  }

  if (!bvid.value.startsWith('BV')) {
    ElMessage.warning('BVID should start with "BV"')
    return
  }

  isSubmitting.value = true
  try {
    const response = await submitAnalysis(bvid.value.trim())
    if (response.code === 0) {
      ElMessage.success('Analysis task submitted successfully!')
      bvid.value = ''
      // Refresh task list
      await fetchTasks()
    } else {
      ElMessage.error(response.message || 'Failed to submit analysis')
    }
  } catch (error: any) {
    console.error('Failed to submit analysis:', error)
    ElMessage.error(error.message || 'Failed to submit analysis')
  } finally {
    isSubmitting.value = false
  }
}

const handleTaskClick = (task: AnalysisTask) => {
  if (task.status === 'COMPLETED') {
    // Navigate to analysis detail page
    router.push(`/analysis/${task.id}`)
  } else {
    ElMessage.info(`Task is ${task.status.toLowerCase()}, please wait for completion`)
  }
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    PENDING: 'info',
    PROCESSING: '',
    COMPLETED: 'success',
    FAILED: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    PENDING: 'Pending',
    PROCESSING: 'Processing',
    COMPLETED: 'Completed',
    FAILED: 'Failed'
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
  fetchTasks()
  if (route.query.bvid) {
    bvid.value = route.query.bvid.toString()
  }
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

.task-card {
  border-radius: var(--radius-lg);
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>

