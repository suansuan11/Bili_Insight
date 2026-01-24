import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layout/MainLayout.vue'
import DashboardView from '@/views/DashboardView.vue'
import PopularVideosView from '@/views/PopularVideosView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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
          path: 'settings',
          name: 'settings',
          component: () => import('@/views/SettingsView.vue'),
        },
      ]
    },
  ],
})

export default router
