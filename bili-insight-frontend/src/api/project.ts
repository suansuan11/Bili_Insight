import request from '@/utils/request'

interface ApiResponse<T> {
    code: number
    message: string
    data: T
}

export interface ProjectData {
    id?: number
    userId?: number
    name: string
    description: string
    keywords: string
    targetBvids: string
    createdAt?: string
    updatedAt?: string
}

export const getProjects = (): Promise<ApiResponse<ProjectData[]>> => {
    return request.get('/insight/projects')
}

export const getProject = (id: number): Promise<ApiResponse<ProjectData>> => {
    return request.get(`/insight/projects/${id}`)
}

export const createProject = (data: ProjectData): Promise<ApiResponse<ProjectData>> => {
    return request.post('/insight/projects', data)
}

export const updateProject = (id: number, data: ProjectData): Promise<ApiResponse<ProjectData>> => {
    return request.put(`/insight/projects/${id}`, data)
}

export const deleteProject = (id: number): Promise<ApiResponse<void>> => {
    return request.delete(`/insight/projects/${id}`)
}
