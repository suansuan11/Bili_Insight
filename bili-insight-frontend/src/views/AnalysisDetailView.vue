<template>
  <div class="analysis-detail-view">
    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-20">
      <el-icon class="is-loading" size="48"><Loading /></el-icon>
      <p class="mt-4 text-gray-500">正在分析视频数据...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-20">
      <el-result icon="error" title="加载失败" :sub-title="error">
        <template #extra>
          <el-button type="primary" @click="fetchAnalysisResult">重试</el-button>
          <el-button @click="$router.push('/analysis')">返回列表</el-button>
        </template>
      </el-result>
    </div>

    <!-- Content -->
    <div v-else-if="result" class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <h1 class="text-2xl font-bold text-gray-800">{{ result.task.title || result.task.bvid }}</h1>
            <el-tag :type="getStatusType(result.task.status)" effect="dark">
              {{ getStatusText(result.task.status) }}
            </el-tag>
          </div>
          <div class="text-sm text-gray-500 flex gap-4">
             <span><el-icon class="mr-1"><VideoPlay /></el-icon> {{ result.task.bvid }}</span>
             <span><el-icon class="mr-1"><Clock /></el-icon> {{ formatDate(result.task.createdAt) }}</span>
          </div>
        </div>
        <el-button @click="$router.push('/analysis')">返回列表</el-button>
      </div>
      
      <!-- Video & Overview Section -->
      <el-row :gutter="24">
        <!-- Left: Video Player -->
        <el-col :lg="14" :md="24" class="mb-6 lg:mb-0">
          <el-card class="video-card" :body-style="{ padding: '0' }">
             <!-- Video Player Iframe: 16:9 aspect ratio -->
             <div class="video-wrapper">
                <iframe 
                   v-if="playerUrl"
                   :src="playerUrl" 
                   scrolling="no" 
                   border="0" 
                   frameborder="no" 
                   framespacing="0" 
                   allowfullscreen="true" 
                ></iframe>
             </div>
          </el-card>
        </el-col>
        
        <!-- Right: Key Statistics -->
        <el-col :lg="10" :md="24">
          <div class="grid grid-cols-2 gap-4">
             <el-card class="stat-card" shadow="hover">
                <div class="stat-content">
                  <div class="stat-icon positive">
                    <el-icon><ChatDotRound /></el-icon>
                  </div>
                  <div>
                    <div class="stat-label">评论总数</div>
                    <div class="stat-value">{{ result.comment_count || 0 }}</div>
                  </div>
                </div>
              </el-card>

              <el-card class="stat-card" shadow="hover">
                <div class="stat-content">
                  <div class="stat-icon neutral">
                    <el-icon><ChatLineRound /></el-icon>
                  </div>
                  <div>
                    <div class="stat-label">弹幕总数</div>
                    <div class="stat-value">{{ result.danmaku_count || 0 }}</div>
                  </div>
                </div>
              </el-card>

              <el-card class="stat-card" shadow="hover">
                <div class="stat-content">
                  <div class="stat-icon positive">
                    <el-icon><CircleCheck /></el-icon>
                  </div>
                  <div>
                    <div class="stat-label">正面反馈</div>
                    <div class="stat-value text-green-500">{{ getPercentage(result.statistics?.positive_ratio) }}</div>
                  </div>
                </div>
              </el-card>

              <el-card class="stat-card" shadow="hover">
                <div class="stat-content">
                  <div class="stat-icon negative">
                    <el-icon><CircleClose /></el-icon>
                  </div>
                  <div>
                    <div class="stat-label">负面反馈</div>
                    <div class="stat-value text-red-500">{{ getPercentage(result.statistics?.negative_ratio) }}</div>
                  </div>
                </div>
              </el-card>
          </div>
        </el-col>
      </el-row>

      <!-- Timeline Chart -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <div class="flex justify-between items-center">
            <div class="font-bold text-lg flex items-center gap-2">
               <el-icon><TrendCharts /></el-icon>
               情绪时间轴 
               <span class="text-xs font-normal text-gray-500 ml-2">(点击折线跳转视频进度)</span>
            </div>
          </div>
        </template>
        <div v-if="hasTimelineData" ref="chartRef" class="chart-container"></div>
        <el-empty v-else description="暂无时间轴数据（弹幕数量不足或分析未完成）" />
      </el-card>

      <!-- Aspect Sentiment Chart (独立一行，全宽居中) -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
           <div class="flex justify-between items-center">
             <span class="font-bold text-lg">切面情感分布</span>
             <el-tooltip content="点击饼图扇区可筛选下方评论" placement="top">
                <el-icon class="text-gray-400"><InfoFilled /></el-icon>
             </el-tooltip>
           </div>
        </template>
        <div v-if="topAspects.length > 0">
          <div ref="aspectChartRef" class="aspect-chart-container-wide"></div>
        </div>
        <el-empty v-else description="暂无切面数据（该视频评论未匹配到分析维度）" :image-size="80" />
      </el-card>

      <!-- Comments and Danmaku Section -->
      <el-card shadow="hover" class="feedback-card">
        <template #header>
          <div class="feedback-header">
            <div class="feedback-title-group">
               <span class="font-bold text-lg text-gray-800">详细反馈</span>
               <el-tag type="info" effect="plain" round class="font-medium px-3">
                  {{ viewMode === 'comments' ? filteredComments.length : filteredDanmakus.length }} 条{{ viewMode === 'comments' ? '评论' : '弹幕' }}
               </el-tag>
            </div>
            
            <div class="feedback-toolbar">
               <el-radio-group v-model="viewMode" size="default" fill="#6366f1">
                  <el-radio-button label="comments">评论列表</el-radio-button>
                  <el-radio-button label="danmaku">弹幕列表</el-radio-button>
               </el-radio-group>
               
               <div class="feedback-filters">
                  <el-select v-model="commentFilter" placeholder="情感筛选" clearable size="default" class="filter-select">
                     <template #prefix><el-icon><Filter /></el-icon></template>
                     <el-option label="全部情感" value="" />
                     <el-option label="😊 正面" value="POSITIVE" />
                     <el-option label="😡 负面" value="NEGATIVE" />
                     <el-option label="😐 中性" value="NEUTRAL" />
                   </el-select>
                   <el-select v-model="aspectFilter" placeholder="话题筛选" clearable size="default" class="filter-select" v-if="viewMode === 'comments'">
                     <template #prefix><el-icon><PriceTag /></el-icon></template>
                     <el-option label="全部话题" value="" />
                     <el-option v-for="aspect in availableAspects" :key="aspect" :label="aspect" :value="aspect" />
                   </el-select>
               </div>
            </div>
          </div>
        </template>
        
        <!-- Comments List -->
        <div v-if="viewMode === 'comments'" class="comments-list" @scroll.passive="handleFeedbackScroll">
          <div v-if="filteredComments.length > 0">
            <div v-for="comment in visibleComments" :key="comment.commentId" class="comment-item hover:bg-gray-50 transition-colors">
              <div class="flex justify-between mb-2">
                 <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-medium text-gray-700">{{ comment.username || comment.author || '用户' }}</span>
                    <el-tag :type="getSentimentTagType(comment.sentimentLabel)" size="small" effect="plain">
                      {{ getSentimentLabelText(comment.sentimentLabel, comment.sentimentIntensity) }}
                    </el-tag>
                    <el-tag
                      v-if="comment.sentimentConfidence !== undefined"
                      size="small"
                      effect="light"
                      type="info"
                    >
                      置信度 {{ formatConfidence(comment.sentimentConfidence) }}
                    </el-tag>
                    <el-tag
                      v-for="detail in getVisibleAspectDetails(comment)"
                      :key="`${comment.commentId}-${detail.aspect}`"
                      :type="getSentimentTagType(detail.label)"
                      size="small"
                      effect="light"
                    >
                      {{ detail.aspect }} {{ getSentimentLabelText(detail.label, deriveIntensity(detail.score)) }}
                    </el-tag>
                    <el-tag
                      v-for="tag in parseEmotionTags(comment.emotionTagsJson)"
                      :key="`${comment.commentId}-${tag}`"
                      size="small"
                      effect="light"
                      type="warning"
                    >
                      {{ formatEmotionTag(tag) }}
                    </el-tag>
                 </div>
                 <span class="text-xs text-gray-400 shrink-0">点赞: {{ comment.likeCount }}</span>
              </div>
              <div class="text-gray-600 leading-relaxed text-sm break-words">{{ comment.content }}</div>
              <div v-if="getAspectContext(comment)" class="mt-2 text-xs text-gray-400">
                关联片段: {{ getAspectContext(comment) }}
              </div>
            </div>
            <div class="feedback-sentinel">
              <span v-if="hasMoreComments">继续下滑加载更多评论</span>
              <span v-else>已经展示全部评论</span>
            </div>
          </div>
          <el-empty v-else description="没有符合条件的评论" />
        </div>

        <!-- Danmaku List -->
        <div v-else class="comments-list" @scroll.passive="handleFeedbackScroll">
           <div v-if="filteredDanmakus.length > 0">
              <div v-for="dm in visibleDanmakus" :key="dm.danmakuId" class="comment-item hover:bg-gray-50 transition-colors flex justify-between items-center">
                 <div class="flex items-center gap-3 flex-1 min-w-0">
                    <el-tag size="small" type="info" effect="dark" class="font-mono">{{ formatTime(dm.dmTime) }}</el-tag>
                    <span class="text-gray-600 text-sm truncate" :title="dm.content">{{ dm.content }}</span>
                 </div>
                 <div class="flex items-center gap-2 ml-2 shrink-0">
                   <el-tag :type="getSentimentTagType(dm.sentimentLabel)" size="small" effect="plain">
                      {{ getSentimentLabelText(dm.sentimentLabel, dm.sentimentIntensity) }}
                   </el-tag>
                   <el-tag v-if="dm.sentimentConfidence !== undefined" size="small" effect="light" type="info">
                      {{ formatConfidence(dm.sentimentConfidence) }}
                   </el-tag>
                 </div>
              </div>
              <div class="feedback-sentinel">
                <span v-if="hasMoreDanmakus">继续下滑加载更多弹幕</span>
                <span v-else>已经展示全部弹幕</span>
              </div>
           </div>
           <el-empty v-else description="没有符合条件的弹幕" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading, ChatDotRound, ChatLineRound, CircleCheck, CircleClose, VideoPlay, Clock, TrendCharts, InfoFilled, Filter, PriceTag } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getAnalysisResult } from '@/api/analysis'
import type { AnalysisResult, VideoComment, VideoDanmaku } from '@/types/analysis'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()
const isLoading = ref(false)
const error = ref<string | null>(null)
const result = ref<AnalysisResult | null>(null)
const chartRef = ref<HTMLElement | null>(null)
const aspectChartRef = ref<HTMLElement | null>(null)

let timelineChart: echarts.ECharts | null = null
let aspectChart: echarts.ECharts | null = null
let resizeHandler: (() => void) | null = null

// Filtering & View State
const viewMode = ref<'comments' | 'danmaku'>('comments')
const commentFilter = ref('')
const aspectFilter = ref('')
const visibleCommentCount = ref(20)
const visibleDanmakuCount = ref(50)
const playerUrl = ref('')
const COMMENT_BATCH_SIZE = 20
const DANMAKU_BATCH_SIZE = 50
type AspectDetail = {
  aspect: string
  label: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  score: number
  confidence?: number
  context?: string
}

// Computed Properties
const availableAspects = computed(() => {
   if (!result.value?.comments) return []
   const aspects = new Set<string>()
   result.value.comments.forEach(c => {
      if (c.aspect) aspects.add(c.aspect)
      parseAspectDetails(c.aspectDetailsJson).forEach(detail => aspects.add(detail.aspect))
   })
   return Array.from(aspects)
})

const topAspects = computed(() => {
  // 优先从 aspectSentimentJson 读取（Python生成的聚合数据）
  if (result.value?.timeline?.aspectSentimentJson) {
    try {
      const aspectData = typeof result.value.timeline.aspectSentimentJson === 'string' 
        ? JSON.parse(result.value.timeline.aspectSentimentJson)
        : result.value.timeline.aspectSentimentJson
      
      return Object.entries(aspectData)
        .map(([aspect, data]: [string, any]) => ({ 
          aspect, 
          count: data.count || 0,
          score: data.score || 0,
          positive: data.positive || 0,
          neutral: data.neutral || 0,
          negative: data.negative || 0,
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10)
    } catch (e) {
      console.error('Failed to parse aspectSentimentJson:', e)
    }
  }
  
  // 降级方案：从评论中统计
  if (!result.value?.comments) return []
  const counts: Record<string, number> = {}
  result.value.comments.forEach(c => {
    if (c.aspect) {
      counts[c.aspect] = (counts[c.aspect] || 0) + 1
    }
  })
  return Object.entries(counts)
    .map(([aspect, count]) => ({ aspect, count, score: 0, positive: 0, neutral: 0, negative: 0 }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const hasTimelineData = computed(() => {
  if (!result.value?.timeline) return false
  const jsonStr = result.value.timeline.timelineJson || result.value.timeline.timelineData
  if (!jsonStr) return false
  try {
    const data = typeof jsonStr === 'string' ? JSON.parse(jsonStr) : jsonStr
    return Array.isArray(data) && data.length > 0
  } catch {
    return false
  }
})

const filteredComments = computed<VideoComment[]>(() => {
  if (!result.value?.comments) return []
  return result.value.comments.filter(c => {
     const matchSentiment = !commentFilter.value || c.sentimentLabel === commentFilter.value
     const matchAspect = !aspectFilter.value || c.aspect === aspectFilter.value || parseAspectDetails(c.aspectDetailsJson).some(detail => detail.aspect === aspectFilter.value)
     return matchSentiment && matchAspect
  })
})

const filteredDanmakus = computed<VideoDanmaku[]>(() => {
   if (!result.value?.danmakus) return []
   return result.value.danmakus.filter(d => {
      const matchSentiment = !commentFilter.value || d.sentimentLabel === commentFilter.value
      return matchSentiment
   })
})

const visibleComments = computed(() => filteredComments.value.slice(0, visibleCommentCount.value))
const visibleDanmakus = computed(() => filteredDanmakus.value.slice(0, visibleDanmakuCount.value))
const hasMoreComments = computed(() => filteredComments.value.length > visibleCommentCount.value)
const hasMoreDanmakus = computed(() => filteredDanmakus.value.length > visibleDanmakuCount.value)

// Methods
const fetchAnalysisResult = async () => {
  const taskId = route.params.id as string
  if (!taskId) {
    error.value = '无效的任务ID'
    return
  }

  isLoading.value = true
  error.value = null
  try {
    const response = await getAnalysisResult(taskId as any)
    if (response.code === 0) {
      result.value = response.data as any
      
      // Initialize Player URL
      if (result.value?.task?.bvid) {
         playerUrl.value = `//player.bilibili.com/player.html?bvid=${result.value.task.bvid}&page=1&high_quality=1&danmaku=0`
      }
      
      await nextTick()
      
      // 延迟渲染确保DOM完全准备好（修复图表不显示的问题）
      setTimeout(() => {
        renderChart()
        renderAspectChart()
      }, 200)
    } else {
      error.value = response.message || '加载失败'
    }
  } catch (err: any) {
    console.error('Failed to fetch analysis result:', err)
    error.value = err.message || '加载失败'
  } finally {
    isLoading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value || !hasTimelineData.value) return

  if (timelineChart) timelineChart.dispose()
  timelineChart = echarts.init(chartRef.value)

  // Parse timeline data - support both field name conventions
  let timelineData: any[] = []
  try {
    const jsonStr = result.value!.timeline!.timelineJson || result.value!.timeline!.timelineData
    if (typeof jsonStr === 'string') {
      timelineData = JSON.parse(jsonStr)
    } else {
      timelineData = jsonStr as any
    }
  } catch (e) {
    console.error('Failed to parse timeline data:', e)
    return
  }

  if (!timelineData || timelineData.length === 0) return

  // Normalize field names: Python stores {time, score, count}, frontend expects {time_point, avg_sentiment}
  const normalized = timelineData.map((item: any) => ({
    time_point: item.time_point ?? item.time ?? 0,
    avg_sentiment: item.avg_sentiment ?? item.score ?? 0.5,
    danmaku_count: item.danmaku_count ?? item.count ?? 0
  }))

  const option = {
    tooltip: { 
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#6366f1', width: 2 } },
      formatter: (params: any) => {
        if (!params || !params.length) return ''
        const item = normalized[params[0].dataIndex]
        return `<strong>${formatTime(item.time_point)}</strong><br/>
                <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:#6366f1;"></span>
                情感均值: ${item.avg_sentiment}<br/>
                <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:#e5e7eb;"></span>
                弹幕数量: ${item.danmaku_count}`
      }
    },
    grid: { left: '40', right: '20', bottom: '30', top: '30', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: normalized.map((item: any) => item.time_point),
      axisLabel: { formatter: (val: any) => formatTime(val) }
    },
    yAxis: {
      type: 'value',
      min: -1,
      max: 1,
      interval: 0.5,
      axisLabel: {
        formatter: (val: number) => {
          if (val === 1) return '强正向'
          if (val === 0.5) return '偏正向'
          if (val === 0) return '中性'
          if (val === -0.5) return '偏负向'
          if (val === -1) return '强负向'
          return String(val)
        }
      },
      splitLine: { lineStyle: { type: 'dashed' } }
    },
    series: [
      {
        name: 'Sentiment',
        type: 'line',
        smooth: 0.3,
        symbol: 'none',
        lineStyle: { width: 3, shadowColor: 'rgba(99, 102, 241, 0.3)', shadowBlur: 10 },
        data: normalized.map((item: any) => item.avg_sentiment),
        itemStyle: { color: '#6366f1' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.0)' }
          ])
        }
      }
    ],
    markLine: {
      silent: true,
      symbol: 'none',
      lineStyle: { color: '#94a3b8', type: 'dashed' },
      data: [{ yAxis: 0 }]
    }
  }

  timelineChart.setOption(option)

  // Interactive: Click to jump video
  timelineChart.on('click', (params) => {
     if (params && params.dataIndex !== undefined) {
        const item = normalized[params.dataIndex]
        jumpToVideo(item.time_point)
     }
  })

  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
  resizeHandler = () => timelineChart?.resize()
  window.addEventListener('resize', resizeHandler)
}

const renderAspectChart = () => {
  if (!aspectChartRef.value || topAspects.value.length === 0) {
    return
  }

  if (aspectChart) aspectChart.dispose()
  aspectChart = echarts.init(aspectChartRef.value)
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: any[]) => {
        const item = topAspects.value[params[0]?.dataIndex ?? 0]
        if (!item) return ''
        return `${item.aspect}<br/>正面: ${item.positive}<br/>中性: ${item.neutral}<br/>负面: ${item.negative}<br/>总数: ${item.count}<br/>平均情感分: ${Number(item.score || 0).toFixed(2)}`
      }
    },
    legend: {
      top: 0,
      data: ['正面', '中性', '负面']
    },
    grid: { left: 80, right: 120, top: 40, bottom: 20, containLabel: true },
    xAxis: {
      type: 'value',
      name: '评论数',
      splitLine: { show: false }
    },
    yAxis: {
      type: 'category',
      data: topAspects.value.map(i => i.aspect),
      inverse: true
    },
    series: [
      {
        name: '正面',
        type: 'bar',
        stack: 'sentiment',
        data: topAspects.value.map(i => i.positive),
        itemStyle: { color: '#22c55e', borderRadius: [0, 0, 0, 0] },
        barWidth: 16
      },
      {
        name: '中性',
        type: 'bar',
        stack: 'sentiment',
        data: topAspects.value.map(i => i.neutral),
        itemStyle: { color: '#94a3b8' },
        barWidth: 16
      },
      {
        name: '负面',
        type: 'bar',
        stack: 'sentiment',
        data: topAspects.value.map(i => i.negative),
        itemStyle: { color: '#ef4444', borderRadius: [0, 6, 6, 0] },
        barWidth: 16,
        label: {
          show: true,
          position: 'right',
          formatter: (params: any) => {
            const item = topAspects.value[params.dataIndex]
            return item ? `${item.count} / ${Number(item.score || 0).toFixed(2)}` : ''
          },
          color: '#64748b',
          fontSize: 12
        }
      }
    ]
  }
  aspectChart.setOption(option)

  // Interactive: Click pie to filter
  aspectChart.on('click', (params) => {
     if (params.name) {
        aspectFilter.value = aspectFilter.value === params.name ? '' : params.name
        viewMode.value = 'comments' // Switch to comments view if not already
        ElMessage.success(aspectFilter.value ? `已筛选切面: ${params.name}` : '已取消筛选')
     }
  })
}

const jumpToVideo = (seconds: number) => {
   if (!result.value?.task?.bvid) return
   // Bilibili iframe supports 't' parameter for time seek (in seconds)
   // Note: To force reload with new time, we update the src. 
   // Adding 'autoplay=1' to ensure it plays immediately.
   const baseUrl = `//player.bilibili.com/player.html?bvid=${result.value.task.bvid}&page=1&high_quality=1&danmaku=0`
   playerUrl.value = `${baseUrl}&t=${Math.floor(seconds)}&autoplay=1`
   ElMessage.success(`已跳转至 ${formatTime(seconds)}`)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTime = (seconds: number) => {
   if (!seconds) return '00:00'
   const m = Math.floor(seconds / 60)
   const s = Math.floor(seconds % 60)
   return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = { PENDING: 'info', RUNNING: '', PROCESSING: '', COMPLETED: 'success', FAILED: 'danger' }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = { PENDING: '等待中', RUNNING: '处理中', PROCESSING: '处理中', COMPLETED: '已完成', FAILED: '失败' }
  return texts[status] || status
}

const getSentimentLabelText = (sentiment: string, intensity?: string) => {
  if (sentiment === 'NEUTRAL') return '中性'
  if (sentiment === 'POSITIVE') {
    return intensity === 'STRONG' ? '强正面' : intensity === 'MEDIUM' ? '偏正面' : '正面'
  }
  if (sentiment === 'NEGATIVE') {
    return intensity === 'STRONG' ? '强负面' : intensity === 'MEDIUM' ? '偏负面' : '负面'
  }
  return sentiment
}

const getSentimentTagType = (sentiment: string) => {
  const types: Record<string, any> = { POSITIVE: 'success', NEGATIVE: 'danger', NEUTRAL: 'info' }
  return types[sentiment] || 'info'
}

const getPercentage = (ratio?: number) => {
  if (ratio === undefined || ratio === null) return '0%'
  return `${(ratio * 100).toFixed(1)}%`
}

const parseAspectDetails = (raw?: string): AspectDetail[] => {
  if (!raw) return []
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const parseEmotionTags = (raw?: string): string[] => {
  if (!raw) return []
  try {
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const getVisibleAspectDetails = (comment: VideoComment): AspectDetail[] => {
  const details = parseAspectDetails(comment.aspectDetailsJson)
  if (details.length > 0) return details.slice(0, 4)
  return comment.aspect
    ? [{ aspect: comment.aspect, label: comment.sentimentLabel, score: comment.sentimentScore || 0 }]
    : []
}

const getAspectContext = (comment: VideoComment) => {
  const details = parseAspectDetails(comment.aspectDetailsJson)
  const first = details.find(item => item.context)
  return first?.context || ''
}

const formatEmotionTag = (tag: string) => {
  const tagMap: Record<string, string> = {
    sarcasm: '反讽',
    complaint: '吐槽',
    praise: '夸赞',
    amused: '调侃',
    disappointment: '失望',
    moved: '感动',
    surprised: '惊艳',
  }
  return tagMap[tag] || tag
}

const formatConfidence = (value?: number) => {
  if (value === undefined || value === null) return '0%'
  return `${Math.round(Number(value) * 100)}%`
}

const deriveIntensity = (score?: number) => {
  const absScore = Math.abs(Number(score || 0))
  if (absScore >= 0.75) return 'STRONG'
  if (absScore >= 0.4) return 'MEDIUM'
  return 'WEAK'
}

const loadMoreComments = () => {
  if (hasMoreComments.value) {
    visibleCommentCount.value += COMMENT_BATCH_SIZE
  }
}

const loadMoreDanmakus = () => {
  if (hasMoreDanmakus.value) {
    visibleDanmakuCount.value += DANMAKU_BATCH_SIZE
  }
}

const handleFeedbackScroll = (event: Event) => {
  const target = event.target as HTMLElement | null
  if (!target) return
  const nearBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 96
  if (!nearBottom) return
  if (viewMode.value === 'comments') {
    loadMoreComments()
  } else {
    loadMoreDanmakus()
  }
}

watch([commentFilter, aspectFilter], () => {
  visibleCommentCount.value = COMMENT_BATCH_SIZE
  visibleDanmakuCount.value = DANMAKU_BATCH_SIZE
})

watch(viewMode, () => {
  visibleCommentCount.value = COMMENT_BATCH_SIZE
  visibleDanmakuCount.value = DANMAKU_BATCH_SIZE
})

onMounted(() => {
  fetchAnalysisResult()
})

onBeforeUnmount(() => {
  timelineChart?.dispose()
  aspectChart?.dispose()
  if (resizeHandler) window.removeEventListener('resize', resizeHandler)
})
</script>

<style scoped>
.video-card {
  border-radius: 12px;
  overflow: hidden;
  background: #000;
  border: none;
}

.video-wrapper {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%; /* 16:9 */
  background: #000;
}

.video-wrapper iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
}

.stat-card, .chart-card {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.positive { background: #ecfdf5; color: #10b981; }
.stat-icon.negative { background: #fef2f2; color: #ef4444; }
.stat-icon.neutral { background: #f3f4f6; color: #6b7280; }

.stat-label { font-size: 0.875rem; color: #6b7280; margin-bottom: 0.25rem; }
.stat-value { font-size: 1.5rem; font-weight: 700; color: #1f2937; }

.chart-container { width: 100%; height: 350px; }
.aspect-chart-container { width: 100%; height: 200px; }
.aspect-chart-container-wide { 
  width: 600px; 
  height: 350px; 
  margin: 0 auto;
}
.feedback-card {
  border-radius: 16px;
}

.feedback-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.feedback-title-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.feedback-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  width: 100%;
}

.feedback-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-select {
  width: 160px;
}

.comments-list {
  max-height: 620px;
  overflow-y: auto;
  border: 1px solid #e6edf8;
  border-radius: 16px;
  background: linear-gradient(180deg, #fcfdff 0%, #ffffff 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.comment-item {
  padding: 18px 20px;
  border-bottom: 1px solid #edf2f7;
  margin-bottom: 0;
}

.comment-item:last-child {
  border-bottom: none;
}

.feedback-sentinel {
  padding: 14px 16px 18px;
  text-align: center;
  color: #94a3b8;
  font-size: 13px;
}

.is-loading { animation: rotating 2s linear infinite; }
@keyframes rotating {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Custom Scrollbar */
.comments-list::-webkit-scrollbar { width: 6px; }
.comments-list::-webkit-scrollbar-thumb { background-color: #e5e7eb; border-radius: 3px; }
.comments-list::-webkit-scrollbar-track { background-color: transparent; }

@media (max-width: 768px) {
  .feedback-toolbar {
    justify-content: flex-start;
  }

  .filter-select {
    width: 100%;
  }

  .aspect-chart-container-wide {
    width: 100%;
    height: 360px;
  }
}
</style>
