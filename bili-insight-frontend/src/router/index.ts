import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'
import DashboardView from '@/views/DashboardView.vue'
import PopularVideosView from '@/views/PopularVideosView.vue'

/**
 * 检查 JWT token 是否已过期（直接解析 payload，无需请求后端）
 */
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    // exp 是秒级时间戳
    return payload.exp * 1000 < Date.now()
  } catch {
    return true
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { public: true }
    },
    {
      path: '/',
      component: MainLayout,
      children: [
        {
          path: '',
          name: 'dashboard',
          component: DashboardView,
        },
        {
          path: 'popular',
          name: 'popular',
          component: PopularVideosView,
        },
        {
          path: 'analysis',
          name: 'analysis',
          component: () => import('@/views/AnalysisView.vue'),
        },
        {
          path: 'analysis/:id',
          name: 'analysis-detail',
          component: () => import('@/views/AnalysisDetailView.vue'),
        },
        {
          path: 'projects',
          name: 'projects',
          component: () => import('@/views/ProjectsView.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
        },
      ]
    },
  ],
})

// 路由守卫：未登录或 token 已过期的用户重定向到登录页
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const isPublicRoute = to.meta.public === true

  if (!isPublicRoute && (!token || isTokenExpired(token))) {
    // token 缺失或已过期，清理并跳转登录
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    next('/login')
  } else if (token && !isTokenExpired(token) && (to.path === '/login' || to.path === '/register')) {
    next('/')
  } else {
    next()
  }
})

export default router
