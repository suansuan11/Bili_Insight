import request from '@/utils/request'

interface ApiResponse<T> {
    code: number
    message: string
    data: T
}

export interface DashboardStats {
    total_videos: number
    total_comments: number
    avg_sentiment: number
    total_tasks: number
    completed_tasks: number
}

export interface DashboardSentimentDistribution {
    counts: Record<string, number>
    intensityBreakdown: Record<string, Record<string, number>>
    total: number
}

export const getDashboardStats = (): Promise<ApiResponse<DashboardStats>> => {
    return request.get('/insight/dashboard/stats')
}

export const getSentimentDistribution = (): Promise<ApiResponse<DashboardSentimentDistribution>> => {
    return request.get('/insight/dashboard/sentiment-distribution')
}

export const getTopAspects = (): Promise<ApiResponse<{ aspect: string, count: number }[]>> => {
    return request.get('/insight/dashboard/top-aspects')
}

export const getTaskTrend = (): Promise<ApiResponse<{ date: string, count: number }[]>> => {
    return request.get('/insight/dashboard/task-trend')
}
