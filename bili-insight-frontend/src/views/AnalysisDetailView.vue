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
          <el-card class="video-card h-full flex flex-col" :body-style="{ padding: '0', flex: 1, display: 'flex' }">
             <!-- Video Player Iframe -->
             <div class="w-full relative bg-black" style="padding-bottom: 56.25%;">
                <iframe 
                   v-if="playerUrl"
                   :src="playerUrl" 
                   scrolling="no" 
                   border="0" 
                   frameborder="no" 
                   framespacing="0" 
                   allowfullscreen="true" 
                   class="absolute top-0 left-0 w-full h-full"
                ></iframe>
             </div>
          </el-card>
        </el-col>
        
        <!-- Right: Key Statistics -->
        <el-col :lg="10" :md="24">
          <div class="grid grid-cols-2 gap-4 h-full">
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

              <!-- Aspect Sentiment Chart (Moved here) -->
              <el-card class="col-span-2 chart-card flex-1" shadow="hover">
                <template #header>
                   <div class="flex justify-between items-center">
                     <span class="font-bold">切面情感分布 (点击筛选)</span>
                     <el-tooltip content="点击饼图扇区可筛选下方评论" placement="top">
                        <el-icon class="text-gray-400"><InfoFilled /></el-icon>
                     </el-tooltip>
                   </div>
                </template>
                <div ref="aspectChartRef" class="h-[200px] w-full"></div>
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
        <div v-if="result.timeline" ref="chartRef" class="chart-container"></div>
        <el-empty v-else description="暂无时间轴数据" />
      </el-card>

      <!-- Comments and Danmaku Section -->
      <el-card shadow="hover">
        <template #header>
          <div class="flex flex-col md:flex-row justify-between items-center gap-4 py-1">
            <div class="flex items-center gap-3 w-full md:w-auto">
               <span class="font-bold text-lg text-gray-800">详细反馈</span>
               <el-tag type="info" effect="plain" round class="font-medium px-3">
                  {{ viewMode === 'comments' ? filteredComments.length : filteredDanmakus.length }} 条{{ viewMode === 'comments' ? '评论' : '弹幕' }}
               </el-tag>
            </div>
            
            <div class="flex flex-wrap items-center gap-3 w-full md:w-auto justify-between md:justify-end">
               <el-radio-group v-model="viewMode" size="default" fill="#6366f1">
                  <el-radio-button label="comments">评论列表</el-radio-button>
                  <el-radio-button label="danmaku">弹幕列表</el-radio-button>
               </el-radio-group>
               
               <div class="flex items-center gap-2">
                  <el-select v-model="commentFilter" placeholder="情感筛选" clearable size="default" class="w-32">
                     <template #prefix><el-icon><Filter /></el-icon></template>
                     <el-option label="全部情感" value="" />
                     <el-option label="😊 正面" value="POSITIVE" />
                     <el-option label="😡 负面" value="NEGATIVE" />
                     <el-option label="😐 中性" value="NEUTRAL" />
                   </el-select>
                   <el-select v-model="aspectFilter" placeholder="话题筛选" clearable size="default" class="w-32" v-if="viewMode === 'comments'">
                     <template #prefix><el-icon><PriceTag /></el-icon></template>
                     <el-option label="全部话题" value="" />
                     <el-option v-for="aspect in availableAspects" :key="aspect" :label="aspect" :value="aspect" />
                   </el-select>
               </div>
            </div>
          </div>
        </template>
        
        <!-- Comments List -->
        <div v-if="viewMode === 'comments'" class="comments-list">
          <div v-if="filteredComments.length > 0">
            <div v-for="comment in filteredComments.slice(0, displayCommentCount)" :key="comment.commentId" class="comment-item hover:bg-gray-50 transition-colors">
              <div class="flex justify-between mb-2">
                 <div class="flex items-center gap-2 flex-wrap">
                    <span class="font-medium text-gray-700">{{ comment.author || '用户' }}</span>
                    <el-tag :type="getSentimentTagType(comment.sentimentLabel)" size="small" effect="plain">
                      {{ getSentimentLabelText(comment.sentimentLabel) }}
                    </el-tag>
                    <el-tag v-if="comment.aspect" type="warning" size="small" effect="light">{{ comment.aspect }}</el-tag>
                 </div>
                 <span class="text-xs text-gray-400 shrink-0">点赞: {{ comment.likeCount }}</span>
              </div>
              <div class="text-gray-600 leading-relaxed text-sm break-words">{{ comment.content }}</div>
            </div>
            <div v-if="filteredComments.length > displayCommentCount" class="text-center mt-4">
              <el-button @click="displayCommentCount += 20" type="primary" link>
                加载更多 (剩余 {{ filteredComments.length - displayCommentCount }})
              </el-button>
            </div>
          </div>
          <el-empty v-else description="没有符合条件的评论" />
        </div>

        <!-- Danmaku List -->
        <div v-else class="comments-list">
           <div v-if="filteredDanmakus.length > 0">
              <div v-for="dm in filteredDanmakus.slice(0, displayCommentCount)" :key="dm.danmakuId" class="comment-item hover:bg-gray-50 transition-colors flex justify-between items-center">
                 <div class="flex items-center gap-3 flex-1 min-w-0">
                    <el-tag size="small" type="info" effect="dark" class="font-mono">{{ formatTime(dm.dmTime) }}</el-tag>
                    <span class="text-gray-600 text-sm truncate" :title="dm.content">{{ dm.content }}</span>
                 </div>
                 <el-tag :type="getSentimentTagType(dm.sentimentLabel)" size="small" effect="plain" class="ml-2 shrink-0">
                      {{ getSentimentLabelText(dm.sentimentLabel) }}
                 </el-tag>
              </div>
              <div v-if="filteredDanmakus.length > displayCommentCount" class="text-center mt-4">
                <el-button @click="displayCommentCount += 50" type="primary" link>
                  加载更多 (剩余 {{ filteredDanmakus.length - displayCommentCount }})
                </el-button>
              </div>
           </div>
           <el-empty v-else description="没有符合条件的弹幕" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
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

// Filtering & View State
const viewMode = ref<'comments' | 'danmaku'>('comments')
const commentFilter = ref('')
const aspectFilter = ref('')
const displayCommentCount = ref(20)
const playerUrl = ref('')

// Computed Properties
const availableAspects = computed(() => {
   if (!result.value?.comments) return []
   const aspects = new Set<string>()
   result.value.comments.forEach(c => {
      if (c.aspect) aspects.add(c.aspect)
   })
   return Array.from(aspects)
})

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

const filteredComments = computed<VideoComment[]>(() => {
  if (!result.value?.comments) return []
  return result.value.comments.filter(c => {
     const matchSentiment = !commentFilter.value || c.sentimentLabel === commentFilter.value
     const matchAspect = !aspectFilter.value || c.aspect === aspectFilter.value
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
      renderChart()
      renderAspectChart()
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
  if (!chartRef.value || !result.value?.timeline) return

  const chart = echarts.init(chartRef.value)
  
  // Parse timeline data
  let timelineData: any[] = []
  try {
    const jsonStr = result.value.timeline.timelineJson || result.value.timeline.timelineData
    if (typeof jsonStr === 'string') {
      timelineData = JSON.parse(jsonStr)
    } else {
      timelineData = jsonStr as any
    }
  } catch (e) {
    console.error('Failed to parse timeline data:', e)
    return
  }

  const option = {
    tooltip: { 
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#6366f1', width: 2 } },
      formatter: (params: any) => {
        if (!params || !params.length) return ''
        const item = timelineData[params[0].dataIndex]
        const timeVal = item.time_point || item.time
        const sentimentVal = item.avg_sentiment ?? item.score
        const countVal = item.danmaku_count ?? item.count
        return `<strong>${formatTime(timeVal)}</strong><br/>
                <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:#6366f1;"></span>
                情感均值: ${sentimentVal}<br/>
                <span style="display:inline-block;margin-right:5px;border-radius:10px;width:10px;height:10px;background-color:#e5e7eb;"></span>
                弹幕数量: ${countVal}`
      }
    },
    grid: { left: '40', right: '20', bottom: '30', top: '30', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timelineData.map((item: any) => item.time_point || item.time),
      axisLabel: { formatter: (val: any) => formatTime(val) }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      splitLine: { lineStyle: { type: 'dashed' } }
    },
    series: [
      {
        name: 'Sentiment',
        type: 'line',
        smooth: 0.3,
        symbol: 'none',
        lineStyle: { width: 3, shadowColor: 'rgba(99, 102, 241, 0.3)', shadowBlur: 10 },
        data: timelineData.map((item: any) => item.avg_sentiment ?? item.score),
        itemStyle: { color: '#6366f1' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.0)' }
          ])
        }
      }
    ]
  }

  chart.setOption(option)
  
  // Interactive: Click to jump video
  chart.on('click', (params) => {
     if (params && params.dataIndex !== undefined) {
        const item = timelineData[params.dataIndex]
        const seconds = item.time_point || item.time
        jumpToVideo(seconds)
     }
  })
  
  window.addEventListener('resize', () => chart.resize())
}

const renderAspectChart = () => {
  if (!aspectChartRef.value || topAspects.value.length === 0) return
  
  const chart = echarts.init(aspectChartRef.value)
  const option = {
    tooltip: { trigger: 'item' },
    legend: { bottom: '0', icon: 'circle', itemWidth: 8, itemHeight: 8 },
    series: [
      {
        name: '切面',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { 
           label: { show: true, fontSize: '14', fontWeight: 'bold' },
           itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
        },
        labelLine: { show: false },
        data: topAspects.value.map(i => ({ value: i.count, name: i.aspect }))
      }
    ]
  }
  chart.setOption(option)
  
  // Interactive: Click pie to filter
  chart.on('click', (params) => {
     if (params.name) {
        aspectFilter.value = aspectFilter.value === params.name ? '' : params.name
        viewMode.value = 'comments' // Switch to comments view if not already
        ElMessage.success(aspectFilter.value ? `已筛选切面: ${params.name}` : '已取消筛选')
     }
  })
  
  window.addEventListener('resize', () => chart.resize())
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

const getSentimentLabelText = (sentiment: string) => {
  const texts: Record<string, string> = { POSITIVE: '正面', NEGATIVE: '负面', NEUTRAL: '中性' }
  return texts[sentiment] || sentiment
}

const getSentimentTagType = (sentiment: string) => {
  const types: Record<string, any> = { POSITIVE: 'success', NEGATIVE: 'danger', NEUTRAL: 'info' }
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
.video-card {
  border-radius: 12px;
  overflow: hidden;
  background: #000;
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
.comments-list { max-height: 600px; overflow-y: auto; }
.comment-item { padding: 1rem; border-bottom: 1px solid #f3f4f6; border-radius: 8px; margin-bottom: 0.5rem; }

.is-loading { animation: rotating 2s linear infinite; }
@keyframes rotating {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Custom Scrollbar */
.comments-list::-webkit-scrollbar { width: 6px; }
.comments-list::-webkit-scrollbar-thumb { background-color: #e5e7eb; border-radius: 3px; }
.comments-list::-webkit-scrollbar-track { background-color: transparent; }
</style>
