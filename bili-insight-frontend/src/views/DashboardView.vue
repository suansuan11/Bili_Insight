<template>
  <div class="dashboard-view">
    <!-- Welcome Banner -->
    <div class="welcome-banner mb-8">
      <div class="welcome-content">
        <div>
          <h2 class="text-2xl font-bold mb-2" style="color: #fff;">欢迎回来，{{ username }}</h2>
          <p style="color: rgba(255,255,255,0.85);">{{ todayDate }} — 来看看你的视频分析动态吧</p>
        </div>
        <div class="welcome-icon">
          <el-icon :size="48" color="rgba(255,255,255,0.3)"><DataAnalysis /></el-icon>
        </div>
      </div>
    </div>

    <!-- Stats Grid -->
    <div v-if="isLoading" class="text-center py-8">
      <el-icon class="is-loading" size="32"><Loading /></el-icon>
      <p class="mt-2 text-gray-500">Loading statistics...</p>
    </div>
    <div v-else class="grid grid-cols-4 gap-6 mb-8">
      <el-card shadow="hover" class="stat-card stat-card-videos border-none">
        <div class="flex flex-col">
          <div class="flex items-center mb-2">
            <div class="stat-icon-bg p-2 rounded-lg mr-3 flex items-center justify-center w-10 h-10">
              <el-icon :size="20" color="#667eea"><VideoPlay /></el-icon>
            </div>
            <div class="stat-label font-medium text-sm">总视频数</div>
          </div>
          <div class="text-3xl font-bold pl-1 stat-value">{{ formatNumber(stats.total_videos) }}</div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card stat-card-comments border-none">
        <div class="flex flex-col">
          <div class="flex items-center mb-2">
            <div class="stat-icon-bg p-2 rounded-lg mr-3 flex items-center justify-center w-10 h-10">
              <el-icon :size="20" color="#f5576c"><ChatLineSquare /></el-icon>
            </div>
            <div class="stat-label font-medium text-sm">分析评论</div>
          </div>
          <div class="text-3xl font-bold pl-1 stat-value">{{ formatNumber(stats.total_comments) }}</div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card stat-card-sentiment border-none">
        <div class="flex flex-col">
          <div class="flex items-center mb-2">
            <div class="stat-icon-bg p-2 rounded-lg mr-3 flex items-center justify-center w-10 h-10">
              <el-icon :size="20" color="#4facfe"><Star /></el-icon>
            </div>
            <div class="stat-label font-medium text-sm">平均情感</div>
          </div>
          <div class="text-3xl font-bold pl-1 stat-value">{{ stats.avg_sentiment?.toFixed(2) || '0.00' }}</div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card stat-card-tasks border-none">
        <div class="flex flex-col">
          <div class="flex items-center mb-2">
            <div class="stat-icon-bg p-2 rounded-lg mr-3 flex items-center justify-center w-10 h-10">
              <el-icon :size="20" color="#43e97b"><DocumentChecked /></el-icon>
            </div>
            <div class="stat-label font-medium text-sm">已完成任务</div>
          </div>
          <div class="text-3xl font-bold pl-1 stat-value">{{ stats.completed_tasks || 0 }}</div>
        </div>
      </el-card>
    </div>

    <!-- Charts Section -->
    <div class="grid grid-cols-3 gap-6">
      <el-card shadow="never" class="col-span-2 border-none glass-card">
        <template #header>
          <div class="flex justify-between items-center">
            <span class="font-bold text-gray-700">Analysis Task Trend</span>
            <el-button link type="primary" @click="$router.push('/analysis')">View All Tasks</el-button>
          </div>
        </template>
        <div ref="trendChartRef" class="h-64"></div>
      </el-card>

      <el-card shadow="never" class="border-none glass-card">
        <template #header>
          <span class="font-bold text-gray-700">Top Keywords / Aspects</span>
        </template>
        <div v-if="topAspects.length > 0" class="space-y-4">
          <div v-for="(item, index) in topAspects" :key="index" class="flex justify-between items-center keyword-item">
            <div class="flex items-center">
              <span class="rank-tag mr-2" :class="'rank-' + (index + 1)">{{ index + 1 }}</span>
              <span class="text-gray-600 font-medium">{{ item.aspect }}</span>
            </div>
            <el-tag size="small" round effect="plain">{{ item.count }} hits</el-tag>
          </div>
        </div>
        <el-empty v-else :image-size="60" description="No keywords found" />
      </el-card>
    </div>

    <!-- Second row of charts -->
    <div class="grid grid-cols-2 gap-6 mt-6">
      <el-card shadow="never" class="border-none glass-card">
        <template #header>
          <span class="font-bold text-gray-700">Global Sentiment Distribution</span>
        </template>
        <div ref="sentimentChartRef" class="h-64"></div>
      </el-card>

      <el-card shadow="never" class="border-none glass-card">
        <template #header>
          <span class="font-bold text-gray-700">Quick Actions</span>
        </template>
        <div class="grid grid-cols-2 gap-4 py-2">
          <!-- New Analysis -->
          <div 
            class="action-card bg-indigo-50 hover:bg-indigo-100 cursor-pointer p-4 rounded-xl flex flex-col justify-center items-center text-center transition-all group"
            @click="$router.push('/analysis')"
          >
            <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center text-indigo-600 mb-3 shadow-sm group-hover:scale-110 transition-transform">
              <el-icon :size="24"><Plus /></el-icon>
            </div>
            <h3 class="font-semibold text-gray-700 mb-1">New Analysis</h3>
            <p class="text-xs text-gray-500">Analyze a specific video</p>
          </div>

          <!-- Explore Popular -->
          <div 
            class="action-card bg-emerald-50 hover:bg-emerald-100 cursor-pointer p-4 rounded-xl flex flex-col justify-center items-center text-center transition-all group"
            @click="triggerPopularScrape"
            v-loading="isScraping"
          >
            <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center text-emerald-600 mb-3 shadow-sm group-hover:scale-110 transition-transform">
              <el-icon :size="24"><Compass /></el-icon>
            </div>
            <h3 class="font-semibold text-gray-700 mb-1">Fetch Popular</h3>
            <p class="text-xs text-gray-500">Update hot video data</p>
          </div>

          <!-- Export Report -->
          <div
            class="action-card bg-blue-50 hover:bg-blue-100 cursor-pointer p-4 rounded-xl flex flex-col justify-center items-center text-center transition-all group"
            @click="exportReportCSV"
          >
             <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center text-blue-500 mb-3 shadow-sm group-hover:scale-110 transition-transform">
              <el-icon :size="24"><Download /></el-icon>
            </div>
            <h3 class="font-semibold text-gray-700 mb-1">导出报告</h3>
            <p class="text-xs text-gray-500">下载CSV分析报告</p>
          </div>

          <!-- Export Report -->
          <div class="action-card bg-amber-50 hover:bg-amber-100 cursor-pointer p-4 rounded-xl flex flex-col justify-center items-center text-center transition-all group">
             <div class="w-12 h-12 bg-white rounded-full flex items-center justify-center text-amber-500 mb-3 shadow-sm group-hover:scale-110 transition-transform">
              <el-icon :size="24"><Download /></el-icon>
            </div>
            <h3 class="font-semibold text-gray-700 mb-1">Export</h3>
            <p class="text-xs text-gray-500">Download report</p>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { VideoPlay, ChatLineSquare, Star, DocumentChecked, Loading, Plus, Compass, Download, DataAnalysis } from '@element-plus/icons-vue'
import { getDashboardStats, getSentimentDistribution, getTopAspects, getTaskTrend, type DashboardStats } from '@/api/dashboard'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '@/utils/request'

// Parse username from JWT in localStorage
const username = computed(() => {
  try {
    const token = localStorage.getItem('token') || ''
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.sub || payload.username || '用户'
    }
  } catch (_) { /* ignore */ }
  return '用户'
})

const todayDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

const isLoading = ref(false)
const isScraping = ref(false)
const trendChartRef = ref<HTMLElement | null>(null)
const sentimentChartRef = ref<HTMLElement | null>(null)

const triggerPopularScrape = async () => {
  if (isScraping.value) return
  isScraping.value = true
  ElMessage.info('正在抓取热门视频...')
  try {
    await request.post('/insight/popular-videos/fetch?pages=5')
    ElMessage.success('热门视频抓取任务已启动！')
  } catch (e) {
    console.error(e)
    ElMessage.error('启动抓取任务失败，请检查服务是否运行')
  } finally {
    setTimeout(() => { isScraping.value = false }, 2000)
  }
}

const stats = ref<Partial<DashboardStats>>({
  total_videos: 0,
  total_comments: 0,
  avg_sentiment: 0,
  total_tasks: 0,
  completed_tasks: 0
})

const topAspects = ref<{ aspect: string, count: number }[]>([])

const fetchStats = async () => {
  isLoading.value = true
  try {
    const [statsRes, sentimentRes, aspectsRes, trendRes] = await Promise.all([
      getDashboardStats(),
      getSentimentDistribution(),
      getTopAspects(),
      getTaskTrend()
    ])

    if (statsRes.code === 0) stats.value = statsRes.data
    if (aspectsRes.code === 0) topAspects.value = aspectsRes.data

    await nextTick()
    
    if (trendRes.code === 0) renderTrendChart(trendRes.data)
    if (sentimentRes.code === 0) renderSentimentChart(sentimentRes.data)

  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
    ElMessage.error('Failed to load dashboard data')
  } finally {
    isLoading.value = false
  }
}

const renderTrendChart = (data: { date: string, count: number }[]) => {
  if (!trendChartRef.value) return
  const chart = echarts.init(trendChartRef.value)
  const option = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(i => i.date.split('T')[0] || i.date),
      axisLine: { lineStyle: { color: '#e5e7eb' } },
      axisLabel: { color: '#9ca3af' }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { type: 'dashed', color: '#f3f4f6' } },
      axisLabel: { color: '#9ca3af' }
    },
    series: [{
      name: 'Created Tasks',
      type: 'line',
      smooth: true,
      data: data.map(i => i.count),
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(79, 70, 229, 0.2)' },
          { offset: 1, color: 'rgba(79, 70, 229, 0)' }
        ])
      },
      itemStyle: { color: '#4f46e5' },
      lineStyle: { width: 3 }
    }]
  }
  chart.setOption(option)
}

const renderSentimentChart = (data: Record<string, number>) => {
  if (!sentimentChartRef.value) return
  const chart = echarts.init(sentimentChartRef.value)
  
  const pieData = [
    { value: data.POSITIVE || 0, name: 'Positive', itemStyle: { color: '#10b981' } },
    { value: data.NEUTRAL || 0, name: 'Neutral', itemStyle: { color: '#fbbf24' } },
    { value: data.NEGATIVE || 0, name: 'Negative', itemStyle: { color: '#ef4444' } }
  ].filter(i => i.value > 0)

  const option = {
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%', left: 'center' },
    series: [{
      name: 'Sentiment',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      data: pieData
    }]
  }
  chart.setOption(option)
}

const formatNumber = (num?: number) => {
  if (!num) return '0'
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`
  if (num >= 1e3) return `${(num / 1e3).toFixed(1)}K`
  return String(num)
}

const exportReportCSV = () => {
  const rows = [
    ['指标', '数值'],
    ['总视频数', String(stats.value.total_videos || 0)],
    ['总评论数', String(stats.value.total_comments || 0)],
    ['平均情感分', String(stats.value.avg_sentiment?.toFixed(2) || '0.00')],
    ['已完成任务', String(stats.value.completed_tasks || 0)],
    ['总任务数', String(stats.value.total_tasks || 0)],
    [],
    ['热门切面', '出现次数'],
    ...topAspects.value.map(a => [a.aspect, String(a.count)])
  ]
  const csvContent = '\uFEFF' + rows.map(r => r.join(',')).join('\n')
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `bili-insight-report-${new Date().toISOString().split('T')[0]}.csv`
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('报告已导出')
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.grid { display: grid; }
.grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.col-span-2 { grid-column: span 2 / span 2; }
.gap-6 { gap: 1.5rem; }
.mb-8 { margin-bottom: 2rem; }
.mt-6 { margin-top: 1.5rem; }
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.flex-col { flex-direction: column; }
.p-2 { padding: 0.5rem; }
.mr-3 { margin-right: 0.75rem; }
.mr-2 { margin-right: 0.5rem; }
.pl-1 { padding-left: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }
.w-10 { width: 2.5rem; }
.h-10 { height: 2.5rem; }
.h-64 { height: 16rem; }
.text-2xl { font-size: 1.5rem; }
.text-3xl { font-size: 1.875rem; }
.text-sm { font-size: 0.875rem; }
.font-bold { font-weight: 700; }
.font-medium { font-weight: 500; }
.text-gray-500 { color: #6b7280; }
.text-gray-600 { color: #4b5563; }
.text-gray-700 { color: #374151; }
.bg-indigo-50 { background-color: #eef2ff; }
.bg-emerald-50 { background-color: #ecfdf5; }
.bg-amber-50 { background-color: #fffbeb; }
.bg-rose-50 { background-color: #fff1f2; }
.text-indigo-600 { color: #4f46e5; }
.text-emerald-600 { color: #10b981; }
.text-amber-600 { color: #d97706; }
.text-rose-600 { color: #e11d48; }

.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-xl);
}

.welcome-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 28px 32px;
  position: relative;
  overflow: hidden;
}

.welcome-banner::after {
  content: '';
  position: absolute;
  top: -30%;
  right: -5%;
  width: 200px;
  height: 200px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 50%;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.welcome-icon {
  opacity: 0.7;
}

.stat-card {
  border-radius: var(--radius-xl);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
}

.stat-card-videos :deep(.el-card__body) { background: linear-gradient(135deg, #667eea, #764ba2); border-radius: var(--radius-xl); }
.stat-card-comments :deep(.el-card__body) { background: linear-gradient(135deg, #f093fb, #f5576c); border-radius: var(--radius-xl); }
.stat-card-sentiment :deep(.el-card__body) { background: linear-gradient(135deg, #4facfe, #00f2fe); border-radius: var(--radius-xl); }
.stat-card-tasks :deep(.el-card__body) { background: linear-gradient(135deg, #43e97b, #38f9d7); border-radius: var(--radius-xl); }

.stat-label {
  color: rgba(255, 255, 255, 0.85);
}

.stat-value {
  color: #ffffff;
}

.stat-icon-bg {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
}

.keyword-item {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  transition: background-color 0.2s;
}

.keyword-item:hover {
  background-color: rgba(79, 70, 229, 0.05);
}

.rank-tag {
  display: inline-flex;
  width: 20px;
  height: 20px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 11px;
  font-weight: bold;
  color: white;
  background: #d1d5db;
}

.rank-1 { background: #fbbf24; }
.rank-2 { background: #94a3b8; }
.rank-3 { background: #b45309; }

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
