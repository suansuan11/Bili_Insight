import request from '@/utils/request'
import type { AnalysisTask, AnalysisResult, VideoComment, VideoDanmaku, SentimentTimeline, PaginatedList } from '@/types/analysis'

// Define the response structure if it's consistent
interface ApiResponse<T> {
    code: number
    message: string
    data: T
}

export const submitAnalysis = (bvid: string): Promise<ApiResponse<{ task_id: number; status: string; message: string }>> => {
    return request.post('/insight/analysis/submit', null, {
        params: { bvid }
    })
}

export const getTaskStatus = (taskId: string): Promise<ApiResponse<AnalysisTask>> => {
    return request.get(`/insight/analysis/status/${taskId}`)
}

export const getTaskByBvid = (bvid: string): Promise<ApiResponse<AnalysisTask>> => {
    return request.get('/insight/analysis/task', {
        params: { bvid }
    })
}

export const getAnalysisResult = (taskId: string): Promise<ApiResponse<AnalysisResult>> => {
    return request.get(`/insight/analysis/result/${taskId}`)
}

export const getComments = (
    taskId: string,
    page: number,
    size: number,
    sentiment?: string,
    aspect?: string
): Promise<ApiResponse<PaginatedList<VideoComment>>> => {
    return request.get(`/insight/analysis/comments/${taskId}`, {
        params: { page, size, sentiment, aspect }
    })
}

export const getDanmakus = (
    taskId: string,
    page: number,
    size: number,
    sentiment?: string
): Promise<ApiResponse<PaginatedList<VideoDanmaku>>> => {
    return request.get(`/insight/analysis/danmakus/${taskId}`, {
        params: { page, size, sentiment }
    })
}

export const getTimeline = (taskId: string): Promise<ApiResponse<SentimentTimeline>> => {
    return request.get(`/insight/analysis/timeline/${taskId}`)
}

export const getRecentTasks = (limit: number = 20): Promise<ApiResponse<AnalysisTask[]>> => {
    return request.get('/insight/analysis/recent', {
        params: { limit }
    })
}
