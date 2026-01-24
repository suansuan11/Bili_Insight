import request from '@/utils/request'
import type { AnalysisTask, AnalysisResult, VideoComment, VideoDanmaku, SentimentTimeline } from '@/types/analysis'

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

export const getTaskStatus = (taskId: number): Promise<ApiResponse<AnalysisTask>> => {
    return request.get(`/insight/analysis/status/${taskId}`)
}

export const getTaskByBvid = (bvid: string): Promise<ApiResponse<AnalysisTask>> => {
    return request.get('/insight/analysis/task', {
        params: { bvid }
    })
}

export const getAnalysisResult = (taskId: number): Promise<ApiResponse<AnalysisResult>> => {
    return request.get(`/insight/analysis/result/${taskId}`)
}

export const getComments = (taskId: number, sentiment?: string, aspect?: string): Promise<ApiResponse<VideoComment[]>> => {
    return request.get(`/insight/analysis/comments/${taskId}`, {
        params: { sentiment, aspect }
    })
}

export const getDanmakus = (taskId: number, sentiment?: string): Promise<ApiResponse<VideoDanmaku[]>> => {
    return request.get(`/insight/analysis/danmakus/${taskId}`, {
        params: { sentiment }
    })
}

export const getTimeline = (taskId: number): Promise<ApiResponse<SentimentTimeline>> => {
    return request.get(`/insight/analysis/timeline/${taskId}`)
}

export const getRecentTasks = (limit: number = 20): Promise<ApiResponse<AnalysisTask[]>> => {
    return request.get('/insight/analysis/recent', {
        params: { limit }
    })
}
