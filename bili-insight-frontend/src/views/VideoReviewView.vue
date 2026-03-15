<template>
  <div class="video-review" v-loading="loading">
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
      <h3>Comments Review</h3>
      <CommentList :comments="comments" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import request from '@/utils/request'
import CommentList from '@/components/CommentList.vue'

const route = useRoute()
const loading = ref(true)
const bvid = ref('')
const timelineJson = ref<any>(null)
const comments = ref<any[]>([])
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const taskId = route.params.id

const fetchTaskData = async () => {
  try {
    const res: any = await request.get(`/insight/api/analysis/task/${taskId}`)
    if (res.code === 0 && res.data) {
      bvid.value = res.data.bvid
      if (res.data.timeline_json) {
        timelineJson.value = JSON.parse(res.data.timeline_json)
        initChart()
      }
    } else {
      ElMessage.error(res.message || 'Failed to fetch task data')
    }
    
    const commentsRes: any = await request.get(`/insight/api/analysis/task/${taskId}/comments`)
    if (commentsRes.code === 0) {
      comments.value = commentsRes.data
    }
  } catch (error: any) {
    ElMessage.error(error.message || 'Error fetching data')
  } finally {
    loading.value = false
  }
}

const initChart = () => {
  if (!chartRef.value || !timelineJson.value) return
  
  chartInstance = echarts.init(chartRef.value)
  
  const timestamps = timelineJson.value.map((item: any) => item.time)
  const sentimentScores = timelineJson.value.map((item: any) => item.score)
  
  const option = {
    title: { text: 'Sentiment Over Time' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: timestamps,
      name: 'Time'
    },
    yAxis: {
      type: 'value',
      name: 'Sentiment Score'
    },
    series: [
      {
        data: sentimentScores,
        type: 'line',
        smooth: true,
        itemStyle: { color: '#409EFF' }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

onMounted(() => {
  fetchTaskData()
  
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
})
</script>

<style scoped>
.video-review {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
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
  border: 1px solid #eba;
}
.comments-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
}
</style>
