import request from '@/utils/request'
import type { LocalSettings } from '@/composables/useUserSettings'

interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface UserSettingsPayload {
  language: string
  dateFormat: string
  desktopNotify: boolean
  soundNotify: boolean
  weeklyReport: boolean
  analysisEngine: string
  dataRetention: string
}

export const getUserSettings = (): Promise<ApiResponse<UserSettingsPayload>> => {
  return request.get('/insight/settings')
}

export const saveUserSettings = (settings: LocalSettings): Promise<ApiResponse<UserSettingsPayload>> => {
  return request.put('/insight/settings', {
    language: settings.language,
    dateFormat: settings.dateFormat,
    desktopNotify: settings.desktopNotify,
    soundNotify: settings.soundNotify,
    weeklyReport: settings.weeklyReport,
    analysisEngine: settings.analysisEngine,
    dataRetention: settings.dataRetention
  })
}

export const getWeeklyReport = (): Promise<ApiResponse<Record<string, unknown>>> => {
  return request.get('/insight/settings/weekly-report')
}
