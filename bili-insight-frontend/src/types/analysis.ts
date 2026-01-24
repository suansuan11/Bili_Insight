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
    rpid: number
    oid: number
    message: string
    sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
    aspect: string
}

export interface VideoDanmaku {
    dmid: string
    content: string
    sentiment: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
    timestamp: number
}

export interface SentimentTimeline {
    taskId: number
    timelineData: string // JSON string, needs parsing in frontend component
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
