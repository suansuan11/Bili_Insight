<template>
  <div class="popular-videos-page">
    <div class="popular-videos-container">
      <header class="page-header">
        <h1 class="page-title">热门视频榜单</h1>
        <p class="page-subtitle">
          Bilibili 当前最火热的视频内容
          <span v-if="videos.length > 0 && videos[0].scrapedAt">
            | 数据截至: {{ videos[0].scrapedAt.slice(0, 16) }}
          </span>
        </p>
      </header>

      <div v-if="isLoading" class="text-center py-20">加载中...</div>

      <div
        v-else-if="error"
        class="bg-red-100 text-red-700 text-center p-4 rounded-lg max-w-xl mx-auto"
      >
        <p class="font-semibold">❌ 加载失败: {{ error }}</p>
      </div>

      <main v-else-if="videos.length > 0" class="space-y-4">
        <div v-for="video in videos" :key="video.bvid" class="video-list-item">
          <!-- 封面 -->
          <div class="thumbnail-container">
            <a
              href="#"
              @click.prevent="showImageModal(video.coverUrl)"
              class="relative block overflow-hidden rounded-md"
            >
              <img
                :src="video.coverUrl"
                :alt="video.title"
                class="thumbnail-image"
                referrerpolicy="no-referrer"
              />
            </a>
            <span class="duration-text"> 视频时长： {{ formatDuration(video.duration) }} </span>
          </div>

          <!-- 信息 -->
          <div class="info-container">
            <div>
              <a
                :href="`https://www.bilibili.com/video/${video.bvid}`"
                target="_blank"
                class="video-title-link"
              >
                <h3 class="video-title" :title="video.title">{{ video.title }}</h3>
              </a>
              <p v-if="video.description" class="video-description">
                {{ video.description }}
              </p>
              <p v-else class="video-description invisible">占位</p>
              <div class="stats-container">
                <span class="stat-item">👁 {{ formatNumber(video.viewCount) }}</span>
                <span class="stat-item">💬 {{ formatNumber(video.danmakuCount) }}</span>
                <span class="stat-item">👍 {{ formatNumber(video.likeCount) }}</span>
              </div>
            </div>
            <div class="author-info flex justify-between items-center w-full">
              <div class="flex flex-col">
                <a
                  :href="`https://space.bilibili.com/${video.authorMid}`"
                  target="_blank"
                  class="author-name"
                  @click.stop
                >
                  @{{ video.author }}
                </a>
                <span class="text-xs text-gray-500">{{ formatRelativeTime(video.publishDate) }}</span>
              </div>
              <el-button type="primary" size="small" round @click.stop="goToAnalyze(video.bvid)">
                立即分析
              </el-button>
            </div>
          </div>
        </div>
      </main>
      <div v-else class="text-center text-gray-500 py-20">暂无热门视频数据</div>
    </div>
    <!-- 【新增】图片灯箱/模态框 -->
    <div v-if="isModalVisible" @click="closeImageModal" class="image-modal-overlay">
      <div class="image-modal-content" @click.stop>
        <img :src="modalImageUrl" alt="Enlarged Image" class="image-modal-img" />
        <div @click="closeImageModal" class="image-modal-close-button" title="关闭">&times;</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import '@/assets/styles/popular-videos.css'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPopularVideos } from '@/api/popular'
import type { VideoInfo } from '@/types/video'

const router = useRouter()
const videos = ref<VideoInfo[]>([])

const goToAnalyze = (bvid: string) => {
  router.push({
    path: '/analysis',
    query: { bvid }
  })
}
const isLoading = ref(true)
const error = ref<string | null>(null)

const fetchPopularVideos = async () => {
  isLoading.value = true
  error.value = null
  try {
    const rawVideos = await getPopularVideos()
    videos.value = rawVideos.map((video) => {
      return video
    })
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : '数据加载失败，请稍后重试。'
  } finally {
    isLoading.value = false
  }
}

onMounted(fetchPopularVideos)

// 【新增】用于控制灯箱的状态
const isModalVisible = ref(false)
const modalImageUrl = ref('')

// 【新增】显示灯箱的方法
const showImageModal = (imageUrl: string) => {
  modalImageUrl.value = imageUrl
  isModalVisible.value = true
}

// 【新增】关闭灯箱的方法
const closeImageModal = () => {
  isModalVisible.value = false
  modalImageUrl.value = ''
}
const formatNumber = (num: number): string =>
  num >= 1e8
    ? (num / 1e8).toFixed(1) + '亿'
    : num >= 1e4
      ? (num / 1e4).toFixed(1) + '万'
      : String(num)

const formatDuration = (s: number): string =>
  s
    ? `${Math.floor(s / 60)
        .toString()
        .padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`
    : '00:00'

const formatRelativeTime = (dateString: string): string => {
  try {
    const now = new Date()
    const past = new Date(dateString.replace(/-/g, '/'))
    const seconds = Math.floor((now.getTime() - past.getTime()) / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)
    const months = Math.floor(days / 30)
    if (seconds < 60) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 30) return `${days}天前`
    if (months < 12) return `${months}月前`
    return `${Math.floor(months / 12)}年前`
  } catch {
    return '未知时间'
  }
}
</script>
