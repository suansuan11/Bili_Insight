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
                  {{ currentFeedbackTotal }} 条{{ viewMode === 'comments' ? '评论' : '弹幕' }}
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
          <div v-if="visibleComments.length > 0" class="comments-grid">
            <div v-for="comment in visibleComments" :key="comment.commentId" class="comment-card shadow-sm hover:shadow-md transition-all">
              <div class="flex mb-3 items-start gap-3">
                <div class="comment-avatar">
                   {{ (comment.username || comment.author || '用')[0].toUpperCase() }}
                </div>
                <div class="comment-author-info">
                  <div class="comment-header-row">
                    <span class="comment-username">{{ comment.username || comment.author || '用户' }}</span>
                    <span class="comment-likes"><el-icon><Star /></el-icon> {{ comment.likeCount || 0 }}</span>
                  </div>
                  <div class="comment-tags">
                    <el-tag :type="getSentimentTagType(comment.sentimentLabel)" size="small" effect="plain" class="modern-tag sentiment-tag">
                      <span class="tag-dot"></span>
                      {{ getSentimentLabelText(comment.sentimentLabel, comment.sentimentIntensity) }}
                    </el-tag>
                    <el-tag
                      v-if="comment.sentimentConfidence !== undefined"
                      size="small"
                      effect="light"
                      type="info"
                      class="modern-tag conf-tag"
                    >
                      置信度 {{ formatConfidence(comment.sentimentConfidence) }}
                    </el-tag>
                    <el-tag
                      v-for="detail in getVisibleAspectDetails(comment)"
                      :key="`${comment.commentId}-${detail.aspect}`"
                      :type="getSentimentTagType(detail.label)"
                      size="small"
                      effect="light"
                      class="modern-tag aspect-tag"
                    >
                      {{ detail.aspect }} {{ getSentimentLabelText(detail.label, deriveIntensity(detail.score)) }}
                    </el-tag>
                    <el-tag
                      v-for="tag in parseEmotionTags(comment.emotionTagsJson)"
                      :key="`${comment.commentId}-${tag}`"
                      size="small"
                      effect="light"
                      type="warning"
                      class="modern-tag emotion-tag"
                    >
                      {{ formatEmotionTag(tag) }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <div class="comment-content-body">{{ comment.content }}</div>
              <div v-if="getAspectContext(comment)" class="comment-context-quote">
                <strong>关联片段:</strong> {{ getAspectContext(comment) }}
              </div>
            </div>
            <div class="feedback-sentinel">
              <span v-if="isLoadingComments">正在加载更多评论...</span>
              <span v-else-if="hasMoreComments">继续下滑加载更多评论</span>
              <span v-else>已经展示全部评论</span>
            </div>
          </div>
          <el-empty v-else description="没有符合条件的评论" />
        </div>

        <!-- Danmaku List -->
        <div v-else class="comments-list" @scroll.passive="handleFeedbackScroll">
           <div v-if="visibleDanmakus.length > 0">
              <div v-for="dm in visibleDanmakus" :key="dm.danmakuId" class="comment-item list-dm flex justify-between items-center">
                 <div class="flex items-center gap-3 flex-1 min-w-0">
                    <el-tag size="small" type="info" effect="dark" class="font-mono dm-time-tag">{{ formatTime(dm.dmTime) }}</el-tag>
                    <span class="dm-content truncate" :title="dm.content">{{ dm.content }}</span>
                 </div>
                 <div class="flex items-center gap-2 ml-2 shrink-0 dm-tags">
                   <el-tag :type="getSentimentTagType(dm.sentimentLabel)" size="small" effect="plain" class="modern-tag sentiment-tag px-2">
                     <span class="tag-dot"></span>
                     {{ getSentimentLabelText(dm.sentimentLabel, dm.sentimentIntensity) }}
                   </el-tag>
                   <el-tag v-if="dm.sentimentConfidence !== undefined" size="small" effect="light" type="info" class="modern-tag conf-tag px-2">
                      {{ formatConfidence(dm.sentimentConfidence) }}
                   </el-tag>
                 </div>
              </div>
              <div class="feedback-sentinel">
                <span v-if="isLoadingDanmakus">正在加载更多弹幕...</span>
                <span v-else-if="hasMoreDanmakus">继续下滑加载更多弹幕</span>
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
import { Loading, ChatDotRound, ChatLineRound, CircleCheck, CircleClose, VideoPlay, Clock, TrendCharts, InfoFilled, Filter, PriceTag, Star } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getAnalysisResult, getComments, getDanmakus } from '@/api/analysis'
import type { AnalysisResult, VideoComment, VideoDanmaku } from '@/types/analysis'
import * as echarts from 'echarts'
import { useDarkMode } from '@/composables/useDarkMode'

const { isDark } = useDarkMode()

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
const comments = ref<VideoComment[]>([])
const danmakus = ref<VideoDanmaku[]>([])
const commentsPage = ref(1)
const danmakusPage = ref(1)
const commentsTotal = ref(0)
const danmakusTotal = ref(0)
const hasMoreComments = ref(true)
const hasMoreDanmakus = ref(true)
const isLoadingComments = ref(false)
const isLoadingDanmakus = ref(false)
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
   const aspects = new Set<string>()
   topAspects.value.forEach(item => aspects.add(item.aspect))
   comments.value.forEach(c => {
      if (c.aspect) aspects.add(c.aspect)
      parseAspectDetails(c.aspectDetailsJson).forEach(detail => aspects.add(detail.aspect))
   })
   return Array.from(aspects).sort()
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
  if (!comments.value.length) return []
  const counts: Record<string, number> = {}
  comments.value.forEach(c => {
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

const visibleComments = computed(() => comments.value)
const visibleDanmakus = computed(() => danmakus.value)
const currentFeedbackTotal = computed(() => viewMode.value === 'comments' ? commentsTotal.value : danmakusTotal.value)

// Methods
const taskId = computed(() => route.params.id as string)

const fetchCommentsPage = async (reset = false) => {
  if (!taskId.value || isLoadingComments.value) return
  isLoadingComments.value = true
  try {
    const targetPage = reset ? 1 : commentsPage.value
    const response = await getComments(taskId.value, targetPage, COMMENT_BATCH_SIZE, commentFilter.value || undefined, aspectFilter.value || undefined)
    if (response.code === 0) {
      const payload = response.data
      commentsTotal.value = payload.total
      hasMoreComments.value = payload.hasMore
      commentsPage.value = payload.page + 1
      comments.value = reset ? payload.items : comments.value.concat(payload.items)
    } else {
      ElMessage.error(response.message || '加载评论失败')
    }
  } catch (err: any) {
    console.error('Failed to fetch comments page:', err)
    ElMessage.error(err.message || '加载评论失败')
  } finally {
    isLoadingComments.value = false
  }
}

const fetchDanmakusPage = async (reset = false) => {
  if (!taskId.value || isLoadingDanmakus.value) return
  isLoadingDanmakus.value = true
  try {
    const targetPage = reset ? 1 : danmakusPage.value
    const response = await getDanmakus(taskId.value, targetPage, DANMAKU_BATCH_SIZE, commentFilter.value || undefined)
    if (response.code === 0) {
      const payload = response.data
      danmakusTotal.value = payload.total
      hasMoreDanmakus.value = payload.hasMore
      danmakusPage.value = payload.page + 1
      danmakus.value = reset ? payload.items : danmakus.value.concat(payload.items)
    } else {
      ElMessage.error(response.message || '加载弹幕失败')
    }
  } catch (err: any) {
    console.error('Failed to fetch danmakus page:', err)
    ElMessage.error(err.message || '加载弹幕失败')
  } finally {
    isLoadingDanmakus.value = false
  }
}

const resetFeedbackList = async () => {
  comments.value = []
  danmakus.value = []
  commentsPage.value = 1
  danmakusPage.value = 1
  hasMoreComments.value = true
  hasMoreDanmakus.value = true
  commentsTotal.value = 0
  danmakusTotal.value = 0

  if (viewMode.value === 'comments') {
    await fetchCommentsPage(true)
  } else {
    await fetchDanmakusPage(true)
  }
}

const fetchAnalysisResult = async () => {
  if (!taskId.value) {
    error.value = '无效的任务ID'
    return
  }

  isLoading.value = true
  error.value = null
  try {
    const response = await getAnalysisResult(taskId.value)
    if (response.code === 0) {
      result.value = response.data as any
      commentsTotal.value = result.value?.comment_count || 0
      danmakusTotal.value = result.value?.danmaku_count || 0
      
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

      await resetFeedbackList()
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

  if (chartRef.value.getAttribute('_echarts_instance_')) {
    echarts.getInstanceByDom(chartRef.value)?.dispose()
  }
  const chart = echarts.init(chartRef.value)
  timelineChart = chart

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
      backgroundColor: isDark.value ? '#1e293b' : '#fff',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#f1f5f9' : '#0f172a' },
      formatter: (params: any) => {
        if (!params || !params.length) return ''
        const item = normalized[params[0].dataIndex]
        const textColor = isDark.value ? '#cbd5e1' : '#475569'
        return `<strong>${formatTime(item.time_point)}</strong><br/>
                <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:#6366f1;"></span>
                <span style="color: ${textColor}; font-size: 13px;">情感均值: ${item.avg_sentiment?.toFixed ? item.avg_sentiment.toFixed(4) : item.avg_sentiment}</span><br/>
                <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:#94a3b8;"></span>
                <span style="color: ${textColor}; font-size: 13px;">弹幕数量: ${item.danmaku_count}</span>`
      }
    },
    grid: { left: '40', right: '20', bottom: '30', top: '30', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: normalized.map((item: any) => item.time_point),
      axisLabel: { formatter: (val: any) => formatTime(val), color: isDark.value ? '#94a3b8' : '#64748b' },
      axisLine: { lineStyle: { color: isDark.value ? '#334155' : '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      min: -1,
      max: 1,
      interval: 0.5,
      axisLabel: {
        color: isDark.value ? '#94a3b8' : '#64748b',
        formatter: (val: number) => {
          if (val === 1) return '强正向'
          if (val === 0.5) return '偏正向'
          if (val === 0) return '中性'
          if (val === -0.5) return '偏负向'
          if (val === -1) return '强负向'
          return String(val)
        }
      },
      splitLine: { lineStyle: { type: 'dashed', color: isDark.value ? '#334155' : '#f1f5f9' } }
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
      backgroundColor: isDark.value ? '#1e293b' : '#fff',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#f1f5f9' : '#0f172a' },
      formatter: (params: any[]) => {
        const item = topAspects.value[params[0]?.dataIndex ?? 0]
        if (!item) return ''
        return `${item.aspect}<br/>正面: ${item.positive}<br/>中性: ${item.neutral}<br/>负面: ${item.negative}<br/>总数: ${item.count}<br/>平均情感分: ${Number(item.score || 0).toFixed(2)}`
      }
    },
    legend: {
      top: 0,
      data: ['正面', '中性', '负面'],
      textStyle: { color: isDark.value ? '#94a3b8' : '#64748b' }
    },
    grid: { left: 80, right: 120, top: 40, bottom: 20, containLabel: true },
    xAxis: {
      type: 'value',
      name: '评论数',
      nameTextStyle: { color: isDark.value ? '#94a3b8' : '#64748b' },
      splitLine: { show: false },
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b' }
    },
    yAxis: {
      type: 'category',
      data: topAspects.value.map(i => i.aspect),
      inverse: true,
      axisLabel: { color: isDark.value ? '#cbd5e1' : '#334155' }
    },
    series: [
      {
        name: '正面',
        type: 'bar',
        stack: 'sentiment',
        data: topAspects.value.map(i => {
           const isLast = (i.neutral === 0 || !i.neutral) && (i.negative === 0 || !i.negative)
           return { value: i.positive, itemStyle: { borderRadius: isLast ? [0, 6, 6, 0] : [0, 0, 0, 0] } }
        }),
        itemStyle: { color: '#22c55e' },
        barWidth: 16
      },
      {
        name: '中性',
        type: 'bar',
        stack: 'sentiment',
        data: topAspects.value.map(i => {
           const isLast = (i.negative === 0 || !i.negative)
           return { value: i.neutral, itemStyle: { borderRadius: isLast ? [0, 6, 6, 0] : [0, 0, 0, 0] } }
        }),
        itemStyle: { color: '#94a3b8' },
        barWidth: 16
      },
      {
        name: '负面',
        type: 'bar',
        stack: 'sentiment',
        data: topAspects.value.map(i => {
           return { value: i.negative, itemStyle: { borderRadius: [0, 6, 6, 0] } }
        }),
        itemStyle: { color: '#ef4444' },
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

watch(isDark, () => {
  renderChart()
  renderAspectChart()
})

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
  if (hasMoreComments.value && !isLoadingComments.value) {
    fetchCommentsPage()
  }
}

const loadMoreDanmakus = () => {
  if (hasMoreDanmakus.value && !isLoadingDanmakus.value) {
    fetchDanmakusPage()
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
  resetFeedbackList()
})

watch(viewMode, () => {
  resetFeedbackList()
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
  padding: 16px;
  border-radius: 12px;
  background: var(--color-bg-base, #f8fafc);
  border: 1px solid var(--color-border);
}

/* Comment Cards List */
.comments-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.comment-card {
  background: var(--color-bg-card, #ffffff);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 20px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.comment-card:hover {
  transform: translateY(-2px);
  border-color: #6366f1;
}

.comment-avatar {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(99, 102, 241, 0.2);
}

.comment-author-info {
  flex: 1;
  min-width: 0;
}

.comment-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.comment-username {
  font-weight: 600;
  font-size: 15px;
  color: var(--color-text-main);
}

.comment-likes {
  font-size: 13px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.comment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Tag Modernization */
.modern-tag {
  border-radius: 8px !important;
  font-weight: 500;
  border: none !important;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px !important;
}

.modern-tag.sentiment-tag {
  background: var(--el-color-success-light-9);
}

.modern-tag.sentiment-tag.el-tag--danger {
  background: var(--el-color-danger-light-9);
}

.modern-tag.sentiment-tag.el-tag--info {
  background: var(--el-color-info-light-9);
}

.tag-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
}

.modern-tag.conf-tag {
  background: var(--color-background-soft);
  color: var(--color-text-light);
  border: 1px solid var(--color-border) !important;
}

.modern-tag.aspect-tag {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.modern-tag.emotion-tag {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.comment-content-body {
  color: var(--color-text-secondary);
  font-size: 14.5px;
  line-height: 1.6;
  margin-bottom: 12px;
  padding-left: 52px;
}

.comment-context-quote {
  margin-left: 52px;
  padding: 10px 14px;
  background: rgba(148, 163, 184, 0.1);
  border-left: 3px solid #6366f1;
  border-radius: 4px 8px 8px 4px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* List Danmaku Mode */
.list-dm {
  background: var(--color-bg-card, #ffffff);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 10px;
}

.list-dm:hover {
  border-color: #6366f1;
}

.dm-time-tag {
  border-radius: 6px !important;
}

.dm-content {
  font-size: 14px;
  color: var(--color-text-main);
  font-weight: 500;
}

.dm-tags {
  display: flex;
  gap: 8px;
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
