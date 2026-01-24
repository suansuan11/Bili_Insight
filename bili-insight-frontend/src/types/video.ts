/**
 * @interface RawVideoInfo
 * 描述从后端API直接获取的、使用下划线命名的原始数据结构
 */
export interface RawVideoInfo {
  bvid: string
  aid: number
  title: string
  author: string
  author_mid: number
  publish_date: string
  duration: number
  view_count: number
  like_count: number
  coin_count: number
  favorite_count: number
  share_count: number
  danmaku_count: number
  comment_count: number
  description: string
  cover_url: string
  scrapedAt: string
}

/**
 * @interface VideoInfo
 * 描述在前端Vue组件中统一使用的、采用驼峰命名的标准数据结构
 */
export interface VideoInfo {
  bvid: string
  aid: number
  title: string
  author: string
  authorMid: number
  publishDate: string
  duration: number
  viewCount: number
  likeCount: number
  coinCount: number
  favoriteCount: number
  shareCount: number
  danmakuCount: number
  commentCount: number
  description: string
  coverUrl: string
  scrapedAt: string
}
