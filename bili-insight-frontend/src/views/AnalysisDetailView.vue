<template>
  <div class="analysis-detail-view">
    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-20">
      <el-icon class="is-loading" size="48"><Loading /></el-icon>
      <p class="mt-4 text-gray-500">Loading analysis results...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-20">
      <el-result icon="error" title="Failed to Load" :sub-title="error">
        <template #extra>
          <el-button type="primary" @click="fetchAnalysisResult">Retry</el-button>
          <el-button @click="$router.push('/analysis')">Back to List</el-button>
        </template>
      </el-result>
    </div>

    <!-- Content -->
    <div v-else-if="result" class="space-y-6">
      <!-- Header -->
      <el-card class="header-card" shadow="hover">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold mb-2">{{ result.task.bvid }}</h1>
            <div class="text-sm text-gray-500">
              Created: {{ formatDate(result.task.createdAt) }}
            </div>
          </div>
          <el-tag :type="getStatusType(result.task.status)" size="large">
            {{ getStatusText(result.task.status) }}
          </el-tag>
        </div>
      </el-card>

      <!-- Statistics Overview -->
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon positive">
                <el-icon><ChatDotRound /></el-icon>
              </div>
              <div>
                <div class="stat-label">Total Comments</div>
                <div class="stat-value">{{ result.comment_count || 0 }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon neutral">
                <el-icon><ChatLineRound /></el-icon>
              </div>
              <div>
                <div class="stat-label">Total Danmakus</div>
                <div class="stat-value">{{ result.danmaku_count || 0 }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon positive">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div>
                <div class="stat-label">Positive</div>
                <div class="stat-value">{{ getPercentage(result.statistics?.positive_ratio) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-icon negative">
                <el-icon><CircleClose /></el-icon>
              </div>
              <div>
                <div class="stat-label">Negative</div>
                <div class="stat-value">{{ getPercentage(result.statistics?.negative_ratio) }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Charts Row -->
      <el-row :gutter="16">
        <el-col :md="16">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="font-bold text-lg">Sentiment Timeline</div>
            </template>
            <div v-if="result.timeline" ref="chartRef" class="chart-container"></div>
            <el-empty v-else description="No timeline data available" />
          </el-card>
        </el-col>
        <el-col :md="8">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <div class="font-bold text-lg">Aspect Distribution</div>
            </template>
            <div ref="aspectChartRef" class="chart-container small"></div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Comments Section -->
      <el-card shadow="hover">
        <template #header>
          <div class="flex justify-between items-center">
            <div class="font-bold text-lg">Comments ({{ result.comments?.length || 0 }})</div>
            <el-select v-model="commentFilter" placeholder="Filter by sentiment" clearable size="small" style="width: 150px">
              <el-option label="All" value="" />
              <el-option label="Positive" value="POSITIVE" />
              <el-option label="Negative" value="NEGATIVE" />
              <el-option label="Neutral" value="NEUTRAL" />
            </el-select>
          </div>
        </template>
        <div v-if="filteredComments.length > 0" class="comments-list">
          <div v-for="comment in filteredComments.slice(0, displayCommentCount)" :key="comment.rpid" class="comment-item">
            <div class="comment-content">{{ comment.message }}</div>
            <div class="comment-meta">
              <el-tag :type="getSentimentTagType(comment.sentiment)" size="small">
                {{ comment.sentiment }}
              </el-tag>
              <span v-if="comment.aspect" class="aspect-tag">{{ comment.aspect }}</span>
            </div>
          </div>
          <div v-if="filteredComments.length > displayCommentCount" class="text-center mt-4">
            <el-button @click="displayCommentCount += 20" type="primary" text>
              Load More ({{ filteredComments.length - displayCommentCount }} remaining)
            </el-button>
          </div>
        </div>
        <el-empty v-else description="No comments available" />
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading, ChatDotRound, ChatLineRound, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getAnalysisResult } from '@/api/analysis'
import type { AnalysisResult, VideoComment } from '@/types/analysis'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()
const isLoading = ref(false)
const error = ref<string | null>(null)
const result = ref<AnalysisResult | null>(null)
const chartRef = ref<HTMLElement | null>(null)
const aspectChartRef = ref<HTMLElement | null>(null)
const commentFilter = ref('')
const displayCommentCount = ref(20)

const topAspects = computed(() => {
  if (!result.value?.comments) return []
  const counts: Record<string, number> = {}
  result.value.comments.forEach(c => {
    if (c.aspect) {
      counts[c.aspect] = (counts[c.aspect] || 0) + 1
    }
  })
  return Object.entries(counts)
    .map(([aspect, count]) => ({ aspect, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const fetchAnalysisResult = async () => {
  const taskId = Number(route.params.id)
  if (!taskId || isNaN(taskId)) {
    error.value = 'Invalid task ID'
    return
  }

  isLoading.value = true
  error.value = null
  try {
    const response = await getAnalysisResult(taskId)
    if (response.code === 0) {
      result.value = response.data as any
      // Render charts after data is loaded
      await nextTick()
      renderChart()
      renderAspectChart()
    } else {
      error.value = response.message || 'Failed to load analysis result'
    }
  } catch (err: any) {
    console.error('Failed to fetch analysis result:', err)
    error.value = err.message || 'Failed to load analysis result'
  } finally {
    isLoading.value = false
  }
}

const filteredComments = computed(() => {
  if (!result.value?.comments) return []
  if (!commentFilter.value) return result.value.comments
  return result.value.comments.filter(c => c.sentiment === commentFilter.value)
})

const renderChart = () => {
  if (!chartRef.value || !result.value?.timeline) return

  const chart = echarts.init(chartRef.value)
  
  // Parse timeline data
  let timelineData: any[] = []
  try {
    if (typeof result.value.timeline.timelineData === 'string') {
      timelineData = JSON.parse(result.value.timeline.timelineData)
    } else {
      timelineData = result.value.timeline.timelineData as any
    }
  } catch (e) {
    console.error('Failed to parse timeline data:', e)
    return
  }

  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['Positive', 'Negative', 'Neutral'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timelineData.map((item: any) => item.time || item.timestamp)
    },
    yAxis: { type: 'value' },
    series: [
      {
        name: 'Positive',
        type: 'line',
        smooth: true,
        data: timelineData.map((item: any) => item.positive || 0),
        itemStyle: { color: '#10b981' }
      },
      {
        name: 'Negative',
        type: 'line',
        smooth: true,
        data: timelineData.map((item: any) => item.negative || 0),
        itemStyle: { color: '#ef4444' }
      },
      {
        name: 'Neutral',
        type: 'line',
        smooth: true,
        data: timelineData.map((item: any) => item.neutral || 0),
        itemStyle: { color: '#6b7280' }
      }
    ]
  }

  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const renderAspectChart = () => {
  if (!aspectChartRef.value || topAspects.value.length === 0) return
  
  const chart = echarts.init(aspectChartRef.value)
  const option = {
    tooltip: { trigger: 'item' },
    series: [
      {
        name: 'Aspects',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: '14', fontWeight: 'bold' } },
        labelLine: { show: false },
        data: topAspects.value.map(i => ({ value: i.count, name: i.aspect }))
      }
    ]
  }
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
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

const getSentimentTagType = (sentiment: string) => {
  const types: Record<string, any> = {
    POSITIVE: 'success',
    NEGATIVE: 'danger',
    NEUTRAL: 'info'
  }
  return types[sentiment] || 'info'
}

const getPercentage = (ratio?: number) => {
  if (ratio === undefined || ratio === null) return '0%'
  return `${(ratio * 100).toFixed(1)}%`
}

onMounted(() => {
  fetchAnalysisResult()
})
</script>

<style scoped>
.space-y-6 > * + * {
  margin-top: 1.5rem;
}

.py-20 {
  padding-top: 5rem;
  padding-bottom: 5rem;
}

.mt-4 {
  margin-top: 1rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.header-card {
  border-radius: var(--radius-lg);
}

.stat-card {
  border-radius: var(--radius-lg);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.positive {
  background: #D1FAE5;
  color: #10b981;
}

.stat-icon.negative {
  background: #FEE2E2;
  color: #ef4444;
}

.stat-icon.neutral {
  background: #E5E7EB;
  color: #6b7280;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.chart-container {
  width: 100%;
  height: 400px;
}

.comments-list {
  max-height: 600px;
  overflow-y: auto;
}

.comment-item {
  padding: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-content {
  margin-bottom: 0.5rem;
  color: #374151;
  line-height: 1.6;
}

.comment-meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.aspect-tag {
  font-size: 0.75rem;
  color: #6b7280;
  background: #f3f4f6;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>
