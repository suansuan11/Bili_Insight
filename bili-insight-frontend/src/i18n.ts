import { createI18n } from 'vue-i18n'

const messages = {
  'zh-CN': {
    nav: {
      dashboard: 'Dashboard',
      popular: '热门视频',
      analysis: '分析任务',
      projects: '监测项目',
      settings: '设置'
    },
    common: {
      analyst: '分析师',
      logout: '退出'
    },
    settings: {
      title: '系统设置',
      subtitle: '配置个人偏好、账号绑定和系统参数',
      tabs: {
        basic: '基本设置',
        account: '账号绑定',
        notifications: '通知设置',
        advanced: '高级设置'
      },
      basic: {
        darkMode: '深色模式',
        darkModeDesc: '启用深色主题界面',
        language: '系统语言',
        languageDesc: '选择系统的主要显示语言',
        dateFormat: '日期时间格式',
        dateFormatDesc: '配置分析任务列表和详情的时间显示格式'
      },
      account: {
        title: 'Bilibili 账号绑定',
        desc: '登录 Bilibili 账号以获取更多评论和弹幕数据，并提高爬虫稳定性。',
        unknownUser: '未知用户',
        logout: '注销账号',
        loggedIn: '已登录',
        fetching: '正在获取用户信息...',
        qrExpired: '二维码已过期',
        qrRefresh: '刷新',
        getQr: '获取登录二维码',
        statusWait: '请使用 Bilibili App 扫码登录',
        statusScanned: '已扫描，请在手机上确认',
        statusConfirmed: '登录成功！',
        statusExpired: '二维码已过期，请刷新'
      },
      notifications: {
        desktop: '桌面通知',
        desktopDesc: '当分析任务状态变更时，向浏览器推送系统通知',
        sound: '任务完成提示音',
        soundDesc: '任务处理完毕后播放清脆的提示音效',
        testSound: '测试',
        dailyReport: '周报推送',
        dailyReportDesc: '每周自动汇总监控数据，当前可在后端生成摘要'
      },
      advanced: {
        engine: '默认分析引擎',
        engineDesc: '选择后续新分析任务使用的底层情感分析引擎',
        engineFast: 'SnowNLP (快速)',
        engineAccurate: 'Transformer (精准)',
        retention: '数据保留期限',
        retentionDesc: '超过期限的已完成或失败分析任务将被自动清理',
        retention30d: '30 天',
        retention90d: '90 天',
        retentionForever: '永不清理'
      }
    }
  },
  'en-US': {
    nav: {
      dashboard: 'Dashboard',
      popular: 'Popular Videos',
      analysis: 'Analysis Tasks',
      projects: 'Tracked Projects',
      settings: 'Settings'
    },
    common: {
      analyst: 'Analyst',
      logout: 'Logout'
    },
    settings: {
      title: 'System Settings',
      subtitle: 'Configure personal preferences, bindings, and parameters',
      tabs: {
        basic: 'Basic Settings',
        account: 'Account Binding',
        notifications: 'Notifications',
        advanced: 'Advanced Settings'
      },
      basic: {
        darkMode: 'Dark Mode',
        darkModeDesc: 'Enable dark theme interface',
        language: 'System Language',
        languageDesc: 'Select the main display language',
        dateFormat: 'Date/Time Format',
        dateFormatDesc: 'Configure time display format for lists and details'
      },
      account: {
        title: 'Bilibili Account Binding',
        desc: 'Log in to your Bilibili account to get more comments/danmaku and improve crawler stability.',
        unknownUser: 'Unknown User',
        logout: 'Logout Account',
        loggedIn: 'Logged In',
        fetching: 'Fetching user info...',
        qrExpired: 'QR Expired',
        qrRefresh: 'Refresh',
        getQr: 'Get Login QR Code',
        statusWait: 'Please scan the code using the Bilibili App',
        statusScanned: 'Scanned, please confirm on your phone',
        statusConfirmed: 'Login successful!',
        statusExpired: 'QR code expired, please refresh'
      },
      notifications: {
        desktop: 'Desktop Notifications',
        desktopDesc: 'Push system notifications to browser when task status changes',
        sound: 'Task Completion Sound',
        soundDesc: 'Play a crisp notification sound when a task completes',
        testSound: 'Test',
        dailyReport: 'Weekly Report Push',
        dailyReportDesc: 'Auto-summarize monitoring data weekly; backend summary is available'
      },
      advanced: {
        engine: 'Default Analysis Engine',
        engineDesc: 'Select the sentiment engine for newly submitted analysis tasks',
        engineFast: 'SnowNLP (Fast)',
        engineAccurate: 'Transformer (Accurate)',
        retention: 'Data Retention Period',
        retentionDesc: 'Expired completed or failed analysis tasks will be auto-cleaned',
        retention30d: '30 Days',
        retention90d: '90 Days',
        retentionForever: 'Keep Forever'
      }
    }
  }
}

export const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  fallbackLocale: 'en-US',
  messages
})
