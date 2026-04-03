<template>
  <div class="dashboard">
    <!-- Page Title Row -->
    <div class="page-title-row">
      <div>
        <h1 class="page-title">数据概览</h1>
        <p class="page-subtitle">{{ todayDate }}，欢迎回来，<strong>{{ username }}</strong></p>
      </div>
      <el-button type="primary" plain size="small" @click="exportReportCSV">
        <el-icon><Download /></el-icon>
        导出报告
      </el-button>
    </div>

    <!-- Stat Cards -->
    <div v-if="isLoading" class="loading-row">
      <el-icon class="spin" :size="28"><Loading /></el-icon>
    </div>
    <div v-else class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon stat-icon--blue">
          <el-icon :size="20"><VideoPlay /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ formatNumber(stats.total_videos) }}</span>
          <span class="stat-label">视频总数</span>
        </div>
        <div class="stat-trend stat-trend--blue"></div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon--violet">
          <el-icon :size="20"><ChatLineSquare /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ formatNumber(stats.total_comments) }}</span>
          <span class="stat-label">已分析评论</span>
        </div>
        <div class="stat-trend stat-trend--violet"></div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon--green">
          <el-icon :size="20"><Star /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ stats.avg_sentiment?.toFixed(2) || '0.00' }}</span>
          <span class="stat-label">平均情感分</span>
        </div>
        <div class="stat-trend stat-trend--green"></div>
      </div>

      <div class="stat-card">
        <div class="stat-icon stat-icon--amber">
          <el-icon :size="20"><DocumentChecked /></el-icon>
        </div>
        <div class="stat-body">
          <span class="stat-value">{{ stats.completed_tasks || 0 }}
            <span class="stat-sub">/ {{ stats.total_tasks || 0 }}</span>
          </span>
          <span class="stat-label">已完成任务</span>
        </div>
        <div class="stat-trend stat-trend--amber"></div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
      <!-- Trend Chart -->
      <div class="chart-card chart-card--wide chart-card--trend">
        <div class="chart-header">
          <span class="chart-title">任务趋势（近7天）</span>
          <button class="chart-link" @click="$router.push('/analysis')">查看全部 →</button>
        </div>
        <div ref="trendChartRef" class="chart-body chart-body--trend"></div>
      </div>

      <!-- Top Aspects -->
      <div class="chart-card chart-card--aspects">
        <div class="chart-header">
          <span class="chart-title">热门切面关键词</span>
        </div>
        <div v-if="topAspects.length > 0" class="aspects-scroll">
          <div class="aspects-list">
            <div v-for="(item, index) in topAspects" :key="index" class="aspect-row">
              <div class="aspect-left">
                <span class="aspect-rank" :class="`rank-${Math.min(index + 1, 3)}`">{{ index + 1 }}</span>
                <span class="aspect-name" :title="item.aspect">{{ item.aspect }}</span>
              </div>
              <span class="aspect-count">{{ item.count }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else :image-size="56" description="暂无数据" />
      </div>
    </div>

    <!-- Second Row -->
    <div class="charts-row">
      <!-- Sentiment Pie -->
      <div class="chart-card chart-card--sentiment">
        <div class="chart-header">
          <span class="chart-title">情感分布</span>
        </div>
        <div ref="sentimentChartRef" class="chart-body chart-body--sentiment"></div>
      </div>

      <!-- Quick Actions -->
      <div class="chart-card chart-card--wide">
        <div class="chart-header">
          <span class="chart-title">快捷操作</span>
        </div>
        <div class="actions-grid">
          <div class="action-item" @click="$router.push('/analysis')">
            <div class="action-icon action-icon--blue">
              <el-icon :size="20"><Plus /></el-icon>
            </div>
            <div class="action-text">
              <p class="action-name">新建分析</p>
              <p class="action-desc">提交视频 BVID 开始分析</p>
            </div>
          </div>

          <div class="action-item" @click="triggerPopularScrape" v-loading="isScraping">
            <div class="action-icon action-icon--green">
              <el-icon :size="20"><Compass /></el-icon>
            </div>
            <div class="action-text">
              <p class="action-name">抓取热门</p>
              <p class="action-desc">更新 B 站热门视频数据</p>
            </div>
          </div>

          <div class="action-item" @click="$router.push('/projects')">
            <div class="action-icon action-icon--violet">
              <el-icon :size="20"><Monitor /></el-icon>
            </div>
            <div class="action-text">
              <p class="action-name">监测项目</p>
              <p class="action-desc">管理品牌监控项目</p>
            </div>
          </div>

          <div class="action-item" @click="$router.push('/popular')">
            <div class="action-icon action-icon--amber">
              <el-icon :size="20"><TrendCharts /></el-icon>
            </div>
            <div class="action-text">
              <p class="action-name">热门榜单</p>
              <p class="action-desc">浏览当前最热视频</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import {
  VideoPlay, ChatLineSquare, Star, DocumentChecked,
  Loading, Plus, Compass, Download, DataAnalysis,
  Monitor, TrendCharts
} from '@element-plus/icons-vue'
import {
  getDashboardStats,
  getSentimentDistribution,
  getTopAspects,
  getTaskTrend,
  type DashboardStats,
  type DashboardSentimentDistribution
} from '@/api/dashboard'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { useDarkMode } from '@/composables/useDarkMode'

const { isDark } = useDarkMode()

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

    if (trendRes.code === 0) {
      lastData.value.trend = trendRes.data
      renderTrendChart(trendRes.data)
    }
    if (sentimentRes.code === 0) {
      lastData.value.sentiment = sentimentRes.data
      renderSentimentChart(sentimentRes.data)
    }

  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  } finally {
    isLoading.value = false
  }
}

const renderTrendChart = (data: { date: string, count: number }[]) => {
  if (!trendChartRef.value) return
  if (trendChartRef.value.getAttribute('_echarts_instance_')) {
    echarts.getInstanceByDom(trendChartRef.value)?.dispose()
  }
  const chart = echarts.init(trendChartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#1e293b', borderColor: '#334155', textStyle: { color: '#f1f5f9' } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '8%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(i => i.date.split('T')[0] || i.date),
      axisLine: { lineStyle: { color: isDark.value ? '#475569' : '#e2e8f0' } },
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { type: 'dashed', color: isDark.value ? '#334155' : '#f1f5f9' } },
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b', fontSize: 12 }
    },
    series: [{
      name: '创建任务',
      type: 'line',
      smooth: false,
      data: data.map(i => i.count),
      symbol: 'circle',
      symbolSize: 6,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(37, 99, 235, 0.15)' },
          { offset: 1, color: 'rgba(37, 99, 235, 0)' }
        ])
      },
      itemStyle: { color: '#2563eb' },
      lineStyle: { width: 2.5, color: '#2563eb' }
    }]
  })
}

const renderSentimentChart = (data: DashboardSentimentDistribution | Record<string, number>) => {
  if (!sentimentChartRef.value) return
  if (sentimentChartRef.value.getAttribute('_echarts_instance_')) {
    echarts.getInstanceByDom(sentimentChartRef.value)?.dispose()
  }
  const chart = echarts.init(sentimentChartRef.value)

  const hasStructuredData = typeof data === 'object' && data !== null && 'counts' in data
  const counts: Record<string, number> = hasStructuredData
    ? (data as DashboardSentimentDistribution).counts
    : (data as Record<string, number>)
  const intensityBreakdown: Record<string, Record<string, number>> | undefined = hasStructuredData
    ? (data as DashboardSentimentDistribution).intensityBreakdown
    : undefined
  const total = hasStructuredData
    ? (data as DashboardSentimentDistribution).total
    : Object.values(counts).reduce((sum, value) => sum + Number(value || 0), 0)

  const pieData = [
    { value: counts.POSITIVE || 0, name: '正面', itemStyle: { color: '#16a34a' } },
    { value: counts.NEUTRAL || 0, name: '中性', itemStyle: { color: '#d97706' } },
    { value: counts.NEGATIVE || 0, name: '负面', itemStyle: { color: '#dc2626' } }
  ].filter(i => i.value > 0)

  const outerRingData = intensityBreakdown
    ? [
        { sentiment: 'POSITIVE', intensity: 'WEAK', label: '正面·轻度', color: '#86efac' },
        { sentiment: 'POSITIVE', intensity: 'MEDIUM', label: '正面·中度', color: '#4ade80' },
        { sentiment: 'POSITIVE', intensity: 'STRONG', label: '正面·强烈', color: '#16a34a' },
        { sentiment: 'NEUTRAL', intensity: 'WEAK', label: '中性·轻度', color: '#fdba74' },
        { sentiment: 'NEUTRAL', intensity: 'MEDIUM', label: '中性·中度', color: '#f59e0b' },
        { sentiment: 'NEUTRAL', intensity: 'STRONG', label: '中性·强烈', color: '#b45309' },
        { sentiment: 'NEGATIVE', intensity: 'WEAK', label: '负面·轻度', color: '#fca5a5' },
        { sentiment: 'NEGATIVE', intensity: 'MEDIUM', label: '负面·中度', color: '#f87171' },
        { sentiment: 'NEGATIVE', intensity: 'STRONG', label: '负面·强烈', color: '#dc2626' }
      ]
        .map(item => ({
          name: item.label,
          value: intensityBreakdown?.[item.sentiment]?.[item.intensity] || 0,
          itemStyle: { color: item.color }
        }))
        .filter(item => item.value > 0)
    : []

  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: '#1e293b',
      borderColor: '#334155',
      textStyle: { color: '#f1f5f9' }
    },
    legend: {
      bottom: '2%',
      left: 'center',
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { color: '#64748b', fontSize: 12 },
      formatter: (name: string) => {
        const item = pieData.find(entry => entry.name === name)
        return item ? `${name} ${item.value}` : name
      }
    },
    title: {
      text: String(total || 0),
      subtext: '评论情感',
      left: 'center',
      top: '34%',
      itemGap: 4,
      textStyle: {
        color: isDark.value ? '#f8fafc' : '#0f172a',
        fontSize: 26,
        fontWeight: 800
      },
      subtextStyle: {
        color: isDark.value ? '#94a3b8' : '#64748b',
        fontSize: 13,
        fontWeight: 500
      }
    },
    graphic: [],
    series: outerRingData.length > 0
      ? [
          {
            name: '主情感',
            type: 'pie',
            radius: ['42%', '58%'],
            center: ['50%', '44%'],
            itemStyle: { borderRadius: 0, borderColor: isDark.value ? '#1e293b' : '#fff', borderWidth: 1 },
            label: { show: false },
            emphasis: { scale: true },
            data: pieData
          },
          {
            name: '情感强度',
            type: 'pie',
            radius: ['64%', '82%'],
            center: ['50%', '44%'],
            itemStyle: { borderRadius: 0, borderColor: isDark.value ? '#1e293b' : '#fff', borderWidth: 1 },
            label: { show: false },
            emphasis: { scale: true },
            data: outerRingData
          }
        ]
      : [{
          name: '情感分布',
          type: 'pie',
          radius: ['52%', '78%'],
          center: ['50%', '44%'],
          itemStyle: { borderRadius: 0, borderColor: isDark.value ? '#1e293b' : '#fff', borderWidth: 1 },
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold', color: isDark.value ? '#f8fafc' : '#0f172a' } },
          data: pieData
        }]
  })
}

const lastData = ref<{trend?: any, sentiment?: any}>({})

watch(isDark, () => {
  if (lastData.value.trend) renderTrendChart(lastData.value.trend)
  if (lastData.value.sentiment) renderSentimentChart(lastData.value.sentiment)
})

const formatNumber = (num?: number) => {
  if (!num) return '0'
  if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`
  if (num >= 1e4) return `${(num / 1e4).toFixed(1)}万`
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
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

/* Page title */
.page-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0 0 4px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Loading */
.loading-row {
  display: flex;
  justify-content: center;
  padding: 32px 0;
  color: #94a3b8;
}

.spin {
  animation: spin 1.4s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ===== Stat Cards ===== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.2s;
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon--blue   { background: #eff6ff; color: #2563eb; }
.stat-icon--violet { background: #f5f3ff; color: #7c3aed; }
.stat-icon--green  { background: #f0fdf4; color: #16a34a; }
.stat-icon--amber  { background: #fffbeb; color: #d97706; }

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-text-main);
  line-height: 1.1;
}

.stat-sub {
  font-size: 14px;
  color: var(--color-text-light);
  font-weight: 400;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Colored accent line on the right edge */
.stat-trend {
  position: absolute;
  right: 0;
  top: 20%;
  bottom: 20%;
  width: 3px;
  border-radius: 2px;
}

.stat-trend--blue   { background: #2563eb; }
.stat-trend--violet { background: #7c3aed; }
.stat-trend--green  { background: #16a34a; }
.stat-trend--amber  { background: #d97706; }

/* ===== Charts ===== */
.charts-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  align-items: start;
}

.chart-card {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.chart-card--wide {
  /* already 2fr from parent grid */
}

.chart-card--trend,
.chart-card--aspects {
  height: 340px;
}

.chart-card--sentiment {
  min-height: 320px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-main);
}

.chart-link {
  font-size: 13px;
  color: #2563eb;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-weight: 500;
  transition: color 0.15s;
}

.chart-link:hover {
  color: #1d4ed8;
}

.chart-body {
  flex: 1;
  min-height: 0;
  height: 220px;
}

.chart-body--trend {
  height: 260px;
}

.chart-body--sentiment {
  height: 280px;
}

/* Aspects list */
.aspects-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 6px;
}

.aspects-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.aspect-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-radius: 8px;
  transition: background 0.15s;
}

.aspect-row:hover {
  background: #f8fafc;
}

.aspect-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.aspect-rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: white;
  background: #cbd5e1;
  flex-shrink: 0;
}

.rank-1 { background: #f59e0b; }
.rank-2 { background: #94a3b8; }
.rank-3 { background: #b87333; }

.aspect-name {
  font-size: 14px;
  color: var(--color-text-main);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.aspect-count {
  font-size: 13px;
  color: var(--color-text-secondary);
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 20px;
  font-weight: 600;
}

.aspects-scroll::-webkit-scrollbar {
  width: 6px;
}

.aspects-scroll::-webkit-scrollbar-thumb {
  background: #dbe3f1;
  border-radius: 999px;
}

.aspects-scroll::-webkit-scrollbar-track {
  background: transparent;
}

/* ===== Quick Actions ===== */
.actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}

.action-item:hover {
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-icon--blue   { background: #eff6ff; color: #2563eb; }
.action-icon--green  { background: #f0fdf4; color: #16a34a; }
.action-icon--violet { background: #f5f3ff; color: #7c3aed; }
.action-icon--amber  { background: #fffbeb; color: #d97706; }

.action-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.action-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-main);
  margin: 0;
}

.action-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Responsive */
@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
