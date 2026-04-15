import { ref, watch } from 'vue'
import { i18n } from '@/i18n'

const SETTINGS_STORAGE_KEY = 'bili-insight-settings'

export interface LocalSettings {
  language: string
  dateFormat: string
  desktopNotify: boolean
  soundNotify: boolean
  dailyReport: boolean
  analysisEngine: string
  dataRetention: string
}

export const defaultSettings: LocalSettings = {
  language: 'zh-CN',
  dateFormat: '1',
  desktopNotify: false,
  soundNotify: false,
  dailyReport: false,
  analysisEngine: 'transformer',
  dataRetention: '90',
}

function loadLocalSettings(): LocalSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY)
    return raw ? { ...defaultSettings, ...JSON.parse(raw) } : defaultSettings
  } catch {
    return defaultSettings
  }
}

// Global reactive state
const settings = ref<LocalSettings>(loadLocalSettings())

// Automatically persist on change
watch(settings, (newSettings) => {
  localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(newSettings))
  if (i18n.global.locale.value !== newSettings.language) {
    i18n.global.locale.value = newSettings.language as any
  }
}, { deep: true, immediate: true })

export function playTestSound() {
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    if (!AudioContextClass) return
    const audioContext = new AudioContextClass()
    const oscillator = audioContext.createOscillator()
    const gain = audioContext.createGain()
    oscillator.type = 'sine'
    oscillator.frequency.value = 880
    gain.gain.value = 0.08
    oscillator.connect(gain)
    gain.connect(audioContext.destination)
    oscillator.start()
    oscillator.stop(audioContext.currentTime + 0.18)
  } catch {
    // Ignore error
  }
}

export function notifyTaskComplete(taskTitle: string, isFailed: boolean = false) {
  if (settings.value.soundNotify) {
    playTestSound()
  }
  if (settings.value.desktopNotify && 'Notification' in window && Notification.permission === 'granted') {
    new Notification('分析任务状态更新', {
      body: `你的视频分析任务「${taskTitle}」已经${isFailed ? '失败' : '完成'}。`,
      icon: '/favicon.ico'
    })
  }
}

export function useUserSettings() {
  const formatDate = (dateStr: string) => {
    if (!dateStr) return ''
    const d = new Date(dateStr)
    const fmt = settings.value.dateFormat
    const yyyy = d.getFullYear()
    const MM = String(d.getMonth() + 1).padStart(2, '0')
    const dd = String(d.getDate()).padStart(2, '0')
    const HH = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')

    if (fmt === '1') {
      return `${yyyy}/${MM}/${dd} ${HH}:${mm}`
    } else if (fmt === '2') {
      return `${yyyy}-${MM}-${dd} ${HH}:${mm}`
    } else if (fmt === '3') {
      return `${MM}月${dd}日 ${HH}:${mm}`
    }
    // fallback
    return d.toLocaleString()
  }

  return {
    settings,
    formatDate
  }
}
