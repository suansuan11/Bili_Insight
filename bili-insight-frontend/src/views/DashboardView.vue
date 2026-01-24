<template>
  <div class="dashboard-view">
    <!-- Welcome Section -->
    <div class="mb-8">
      <h2 class="text-2xl font-bold mb-2">Welcome back!</h2>
      <p class="text-gray-500">Here's what's happening with your video analysis.</p>
    </div>

    <!-- Stats Grid -->
    <div v-if="isLoading" class="text-center py-8">
      <el-icon class="is-loading" size="32"><Loading /></el-icon>
      <p class="mt-2 text-gray-500">Loading statistics...</p>
    </div>
    <div v-else class="grid grid-cols-4 gap-6 mb-8">
      <el-card shadow="hover" class="stat-card border-none">
        <div class="flex flex-col">
          <div class="flex items-center mb-2">
            <div class="icon-bg bg-indigo-50 text-indigo-600 p-2 rounded-lg mr-3 flex items-center justify-center w-10 h-10">
              <el-icon :size="20"><VideoPlay /></el-icon>
            </div>
            <div class="text-gray-500 font-medium text-sm"> Total Videos: </div>
          </div>
          <div class="text-3xl font-bold pl-1 text-gray-800">{{ formatNumber(stats.total_videos) }}</div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card border-none">
        <div class="flex flex-col">
          <div class="flex items-center mb-2">
            <div class="icon-bg bg-emerald-50 text-emerald-600 p-2 rounded-lg mr-3 flex items-center justify-center w-10 h-10">
              <el-icon :size="20"><ChatLineSquare /></el-icon>
            </div>
            <div class="text-gray-500 font-medium text-sm"> Analyzed Comments: </div>
          </div>
          <div class="text-3xl font-bold pl-1 text-gray-800">{{ formatNumber(stats.total_comments) }}</div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card border-none">
        <div class="flex flex-col">
          <div class="flex items-center mb-2">
            <div class="icon-bg bg-amber-50 text-amber-600 p-2 rounded-lg mr-3 flex items-center justify-center w-10 h-10">
              <el-icon :size="20"><Star /></el-icon>
            </div>
            <div class="text-gray-500 font-medium text-sm"> Avg Sentiment: </div>
          </div>
          <div class="text-3xl font-bold pl-1 text-gray-800">{{ stats.avg_sentiment?.toFixed(2) || '0.00' }}</div>
        </div>
      </el-card>

      <el-card shadow="hover" class="stat-card border-none">
        <div class="flex flex-col">
          <div class="flex items-center mb-2">
            <div class="icon-bg bg-rose-50 text-rose-600 p-2 rounded-lg mr-3 flex items-center justify-center w-10 h-10">
              <el-icon :size="20"><DocumentChecked /></el-icon>
            </div>
            <div class="text-gray-500 font-medium text-sm">Completed Tasks</div>
          </div>
          <div class="text-3xl font-bold pl-1 text-gray-800">{{ stats.completed_tasks || 0 }}</div>
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
        <div class="flex flex-col gap-4 py-4">
          <el-button type="primary" size="large" @click="$router.push('/analysis')">
            <el-icon class="mr-2"><Plus /></el-icon> New Analysis
          </el-button>
          <el-button type="success" size="large" @click="$router.push('/popular')">
            <el-icon class="mr-2"><Compass /></el-icon> Explore Popular
          </el-button>
          <el-button type="warning" size="large" plain>
            <el-icon class="mr-2"><Download /></el-icon> Export Global Report
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { VideoPlay, ChatLineSquare, Star, DocumentChecked, Loading, Plus, Compass, Download } from '@element-plus/icons-vue'
import { getDashboardStats, getSentimentDistribution, getTopAspects, getTaskTrend, type DashboardStats } from '@/api/dashboard'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const isLoading = ref(false)
const trendChartRef = ref<HTMLElement | null>(null)
const sentimentChartRef = ref<HTMLElement | null>(null)

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

.stat-card {
  border-radius: var(--radius-xl);
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
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
