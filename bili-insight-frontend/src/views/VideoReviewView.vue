<template>
  <div class="video-review" v-loading="loading">
    <!-- 视频信息头部 -->
    <div class="page-header" v-if="taskInfo">
      <div class="header-content">
        <div class="header-left">
          <el-tag type="info" size="large">{{ taskInfo.bvid }}</el-tag>
          <h2 class="page-title">视频舆情分析</h2>
        </div>
        <el-button type="primary" @click="exportComments" :icon="Download">
          导出数据
        </el-button>
      </div>
    </div>

    <div class="content-grid">
      <!-- 视频播放器 -->
      <div class="player-card">
        <div class="card-header">
          <span class="card-title">视频播放</span>
        </div>
        <div class="video-container">
          <iframe
            v-if="bvid"
            :src="'//player.bilibili.com/player.html?bvid=' + bvid + '&autoplay=0'"
            scrolling="no"
            border="0"
            frameborder="no"
            framespacing="0"
            allowfullscreen="true">
          </iframe>
        </div>
      </div>

      <!-- 情绪时间轴 -->
      <div class="chart-card">
        <div class="card-header">
          <span class="card-title">情绪时间轴</span>
          <el-tag size="small" type="success">实时联动</el-tag>
        </div>
        <div ref="chartRef" class="chart-body"></div>
      </div>
    </div>

    <!-- 评论分析 -->
    <div class="comments-card">
      <div class="card-header">
        <span class="card-title">评论舆情分析</span>
        <span class="comment-count">共 {{ comments.length }} 条评论</span>
      </div>
      <CommentList :comments="comments" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getAnalysisResult, getComments, getTimeline } from '@/api/analysis'
import CommentList from '@/components/CommentList.vue'

const route = useRoute()
const loading = ref(true)
const bvid = ref('')
const taskInfo = ref<any>(null)
const comments = ref<any[]>([])
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const taskId = route.params.id as string

const fetchTaskData = async () => {
  try {
    // 1. 获取任务结果
    const resultRes: any = await getAnalysisResult(taskId as any)
    if (resultRes.code === 0 && resultRes.data) {
      taskInfo.value = resultRes.data.task
      bvid.value = resultRes.data.task?.bvid
    }

    // 2. 获取时间轴数据
    const timelineRes: any = await getTimeline(taskId as any)
    if (timelineRes.code === 0 && timelineRes.data) {
      const timelineData = timelineRes.data.timelineJson || timelineRes.data.timeline_json
      if (timelineData) {
        const timeline = typeof timelineData === 'string' ? JSON.parse(timelineData) : timelineData
        initChart(timeline)
      }
    }

    // 3. 获取评论列表
    const commentsRes: any = await getComments(taskId as any, 1, 200)
    if (commentsRes.code === 0 && commentsRes.data) {
      comments.value = commentsRes.data.items || []
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取数据失败')
  } finally {
    loading.value = false
  }
}

const initChart = (timeline: any[]) => {
  if (!chartRef.value || !timeline || timeline.length === 0) return

  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)

  const timestamps = timeline.map((item: any) => {
    const seconds = item.time
    const min = Math.floor(seconds / 60)
    const sec = seconds % 60
    return `${min}:${sec.toString().padStart(2, '0')}`
  })
  const sentimentScores = timeline.map((item: any) => item.score)

  const option = {
    title: { text: '情绪时间轴', left: 'center' },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = params[0]
        return `时间: ${p.name}<br/>情感得分: ${p.value}<br/>弹幕数: ${timeline[p.dataIndex]?.count || 0}`
      }
    },
    xAxis: {
      type: 'category',
      data: timestamps,
      name: '视频时间',
      axisLabel: { rotate: 45 }
    },
    yAxis: {
      type: 'value',
      name: '情感得分',
      min: 0,
      max: 1
    },
    series: [
      {
        data: sentimentScores,
        type: 'line',
        smooth: true,
        areaStyle: { opacity: 0.3 },
        itemStyle: { color: '#409EFF' },
        markLine: {
          data: [
            { yAxis: 0.6, name: '正面阈值', lineStyle: { color: '#67C23A' } },
            { yAxis: 0.4, name: '负面阈值', lineStyle: { color: '#F56C6C' } }
          ]
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleResize = () => {
  chartInstance?.resize()
}

const exportComments = () => {
  const token = localStorage.getItem('token')
  const url = `http://localhost:8080/insight/export/comments/${taskId}`
  const a = document.createElement('a')
  a.href = url
  a.download = `comments_${taskId}.csv`
  a.click()
}

onMounted(() => {
  fetchTaskData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})
</script>

<style scoped>
.video-review {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.player-card,
.chart-card,
.comments-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  overflow: hidden;
}

.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.video-container {
  aspect-ratio: 16/9;
  background: #000;
}

.video-container iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.chart-body {
  height: 400px;
  padding: 20px;
}

.comment-count {
  font-size: 14px;
  color: #909399;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}
</style>
