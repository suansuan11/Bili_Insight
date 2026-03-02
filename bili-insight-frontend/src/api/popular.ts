import request from '@/utils/request'
import type { VideoInfo, RawVideoInfo } from '@/types/video'

/**
 * 后端返回的统一响应体结构
 */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

/**
 * 异步函数：获取热门视频列表
 * @returns Promise<VideoInfo[]> 返回一个符合前端驼峰命名规范的视频数组
 */
export async function getPopularVideos(): Promise<VideoInfo[]> {
  const response: ApiResponse<RawVideoInfo[]> = await request.get('/insight/popular-videos')

  if (response.code !== 0) {
    throw new Error(response.message || '获取热门视频数据失败')
  }

  const formattedVideos: VideoInfo[] = response.data.map((rawVideo: RawVideoInfo) => {
    return {
      bvid: rawVideo.bvid,
      aid: rawVideo.aid,
      title: rawVideo.title,
      author: rawVideo.author,
      authorMid: rawVideo.author_mid,
      publishDate: rawVideo.publish_date,
      duration: rawVideo.duration,
      viewCount: rawVideo.view_count,
      likeCount: rawVideo.like_count,
      coinCount: rawVideo.coin_count,
      favoriteCount: rawVideo.favorite_count,
      shareCount: rawVideo.share_count,
      danmakuCount: rawVideo.danmaku_count,
      commentCount: rawVideo.comment_count,
      description: rawVideo.description,
      coverUrl: rawVideo.cover_url,
      scrapedAt: rawVideo.scrapedAt,
    }
  })

  return formattedVideos
}



export async function triggerPopularFetch(): Promise<ApiResponse<{ status: string; message: string }>> {
  return request.post('/insight/popular-videos/refresh')
}


export interface PopularFetchStatus {
  running: boolean
  last_result: {
    status: string
    count?: number
    total?: number
    first_error?: string | null
    error?: string
  }
}

export async function getPopularFetchStatus(): Promise<ApiResponse<PopularFetchStatus>> {
  return request.get('/insight/popular-videos/refresh/status')
}
