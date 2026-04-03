export interface AnalysisTask {
    id: string          // backend returns String taskId mapped via @JsonProperty("id")
    bvid: string
    title?: string
    coverUrl?: string
    commentFetchMode?: string
    commentRiskControlled?: boolean
    commentFetchRetries?: number
    status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
    progress?: number
    currentStep?: string
    errorMessage?: string
    createdAt: string
    updatedAt: string
}

export interface VideoComment {
    commentId: number
    taskId: string
    bvid: string
    content: string
    sentimentLabel: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
    sentimentScore: number
    sentimentConfidence?: number
    sentimentIntensity?: 'WEAK' | 'MEDIUM' | 'STRONG'
    sentimentSource?: string
    sentimentVersion?: string
    emotionTagsJson?: string
    aspectDetailsJson?: string
    aspect?: string
    username?: string
    author?: string
    likeCount?: number
}

export interface VideoDanmaku {
    danmakuId: number
    taskId: string
    bvid: string
    content: string
    sentimentLabel: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
    sentimentScore: number
    sentimentConfidence?: number
    sentimentIntensity?: 'WEAK' | 'MEDIUM' | 'STRONG'
    sentimentSource?: string
    sentimentVersion?: string
    emotionTagsJson?: string
    dmTime: number
}

export interface SentimentTimeline {
    taskId: number
    timelineJson: string
    aspectSentimentJson: string
    aggregationMetaJson?: string
    // Backward compatibility if needed, but we should rely on timelineJson
    timelineData?: string
}

export interface AnalysisResult {
    task: AnalysisTask
    timeline: SentimentTimeline
    comment_count?: number
    danmaku_count?: number
    statistics?: {
        positive_count: number
        negative_count: number
        neutral_count: number
        positive_ratio: number
        negative_ratio: number
    }
}

export interface PaginatedList<T> {
    items: T[]
    page: number
    size: number
    total: number
    hasMore: boolean
}
