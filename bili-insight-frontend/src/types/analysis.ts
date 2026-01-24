export interface AnalysisTask {
    id: number
    bvid: string
    title: string
    coverUrl: string
    status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
    progress?: number
    currentStep?: string
    errorMessage?: string
    createdAt: string
    updatedAt: string
}

export interface VideoComment {
    commentId: number
    taskId: number
    bvid: string
    // content maps to 'message' conceptually
    content: string
    // sentimentLabel maps to 'sentiment'
    sentimentLabel: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
    sentimentScore: number
    aspect?: string
    author?: string
    likeCount?: number
}

export interface VideoDanmaku {
    danmakuId: number
    taskId: number
    bvid: string
    content: string
    sentimentLabel: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
    sentimentScore: number
    dmTime: number
}

export interface SentimentTimeline {
    taskId: number
    timelineJson: string
    aspectSentimentJson: string
    // Backward compatibility if needed, but we should rely on timelineJson
    timelineData?: string
}

export interface AnalysisResult {
    task: AnalysisTask
    comments: VideoComment[]
    danmakus: VideoDanmaku[]
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
