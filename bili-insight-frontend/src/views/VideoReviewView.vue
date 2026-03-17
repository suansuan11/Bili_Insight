<template>
  <div class="video-review" v-loading="loading">
    <!-- 视频信息头部 -->
    <div class="video-info-header" v-if="taskInfo">
      <h2>{{ taskInfo.bvid }} - 舆情分析详情</h2>
    </div>

    <div class="top-section">
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
      <div class="chart-container" ref="chartRef"></div>
    </div>

    <div class="comments-section">
      <h3>评论舆情分析</h3>
      <CommentList :comments="comments" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
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
      taskInfo.value = resultRes.data
      bvid.value = resultRes.data.bvid
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
    const commentsRes: any = await getComments(taskId as any)
    if (commentsRes.code === 0 && commentsRes.data) {
      comments.value = commentsRes.data
    }
  } catch (error: any) {
    ElMessage.error(error.message || '获取数据失败')
  } finally {
    loading.value = false
  }
}

const initChart = (timeline: any[]) => {
  if (!chartRef.value || !timeline || timeline.length === 0) return

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
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}
.video-info-header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}
.top-section {
  display: flex;
  gap: 20px;
  height: 500px;
}
.video-container {
  flex: 1;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}
.video-container iframe {
  width: 100%;
  height: 100%;
}
.chart-container {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  border: 1px solid #ebeef5;
}
.comments-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}
</style>
