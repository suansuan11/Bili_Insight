<template>
  <div class="app-shell">
    <!-- Dark Sidebar -->
    <aside class="sidebar" :class="{ 'sidebar--collapsed': isCollapsed }">
      <!-- Logo -->
      <div class="sidebar-logo">
        <div class="logo-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <rect x="3" y="3" width="7" height="7" rx="2" fill="#3b82f6"/>
            <rect x="14" y="3" width="7" height="7" rx="2" fill="#60a5fa" opacity="0.7"/>
            <rect x="3" y="14" width="7" height="7" rx="2" fill="#60a5fa" opacity="0.7"/>
            <rect x="14" y="14" width="7" height="7" rx="2" fill="#3b82f6"/>
          </svg>
        </div>
        <span v-if="!isCollapsed" class="logo-text">Bili Insight</span>
        <button class="collapse-btn" @click="isCollapsed = !isCollapsed" :title="isCollapsed ? '展开' : '收起'">
          <el-icon :size="16">
            <component :is="isCollapsed ? Expand : Fold" />
          </el-icon>
        </button>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ 'nav-item--active': $route.path === item.path }"
          :title="isCollapsed ? item.label : ''"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span v-if="!isCollapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- User Footer -->
      <div class="sidebar-footer">
        <div class="user-row">
          <div class="user-avatar">
            <el-icon :size="14"><User /></el-icon>
          </div>
          <div v-if="!isCollapsed" class="user-meta">
            <span class="user-name">{{ sidebarUsername }}</span>
            <span class="user-role">分析师</span>
          </div>
        </div>
        <button class="logout-btn" @click="handleLogout" :title="isCollapsed ? '退出' : ''">
          <el-icon :size="15"><SwitchButton /></el-icon>
          <span v-if="!isCollapsed">退出</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <div class="main-wrapper">
      <main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Odometer, TrendCharts, DataAnalysis, Monitor, Setting, User, Fold, Expand, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const isCollapsed = ref(false)

const navItems = [
  { path: '/', label: 'Dashboard', icon: Odometer },
  { path: '/popular', label: '热门视频', icon: TrendCharts },
  { path: '/analysis', label: '分析任务', icon: DataAnalysis },
  { path: '/projects', label: '监测项目', icon: Monitor },
  { path: '/settings', label: '设置', icon: Setting },
]

const sidebarUsername = computed(() => {
  try {
    const token = localStorage.getItem('token') || ''
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.sub || payload.username || '用户'
    }
  } catch (_) { /* ignore */ }
  return '用户'
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
</script>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  background: var(--color-sidebar-bg);
  overflow: hidden;
}

/* ===== Sidebar ===== */
.sidebar {
  width: 220px;
  min-width: 220px;
  display: flex;
  flex-direction: column;
  background: var(--color-sidebar-bg);
  transition: width 0.25s ease, min-width 0.25s ease;
  overflow: hidden;
}

.sidebar--collapsed {
  width: 64px;
  min-width: 64px;
}

/* Logo */
.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  flex-shrink: 0;
  position: relative;
}

.logo-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 0.3px;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
}

.collapse-btn {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
  margin-left: auto;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #94a3b8;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.07);
  color: #e2e8f0;
}

.nav-item--active {
  background: rgba(59, 130, 246, 0.18);
  color: #93c5fd;
}

.nav-item--active:hover {
  background: rgba(59, 130, 246, 0.22);
  color: #bfdbfe;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Footer */
.sidebar-footer {
  padding: 12px 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex-shrink: 0;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  overflow: hidden;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: rgba(59, 130, 246, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #60a5fa;
  flex-shrink: 0;
}

.user-meta {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11px;
  color: #64748b;
  margin-top: 1px;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.logout-btn:hover {
  background: rgba(220, 38, 38, 0.12);
  color: #f87171;
}

/* ===== Main Content ===== */
.main-wrapper {
  flex: 1;
  background: var(--color-bg-base);
  border-radius: 16px 0 0 16px;
  margin: 10px 0 10px 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 28px 32px;
}

/* Page transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
