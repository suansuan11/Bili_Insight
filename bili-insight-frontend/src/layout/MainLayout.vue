<template>
  <div class="app-container">
    <el-container class="h-screen" style="background: #ffffff;">
      <!-- Sidebar -->
      <el-aside :width="isCollapsed ? '64px' : '240px'" class="glass-sidebar" style="transition: width 0.3s ease;">
        <div class="logo-area">
          <h1 v-if="!isCollapsed" class="text-xl font-bold"
              style="background: linear-gradient(to right, #6366f1, #8b5cf6); -webkit-background-clip: text; background-clip: text; color: transparent;">
            Bili Insight
          </h1>
          <h1 v-else class="text-xl font-bold"
              style="background: linear-gradient(to right, #6366f1, #8b5cf6); -webkit-background-clip: text; background-clip: text; color: transparent;">
            BI
          </h1>
          <el-button
            :icon="isCollapsed ? Expand : Fold"
            class="collapse-btn"
            text
            @click="isCollapsed = !isCollapsed"
          />
        </div>

        <el-menu
          router
          :default-active="$route.path"
          :collapse="isCollapsed"
          class="custom-menu"
          background-color="transparent"
          text-color="#64748b"
          active-text-color="#6366f1"
        >
          <el-menu-item index="/">
            <el-icon><Odometer /></el-icon>
            <template #title>Dashboard</template>
          </el-menu-item>

          <el-menu-item index="/popular">
            <el-icon><TrendCharts /></el-icon>
            <template #title>Popular Videos</template>
          </el-menu-item>

          <el-menu-item index="/analysis">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>Analysis</template>
          </el-menu-item>

          <el-menu-item index="/projects">
            <el-icon><Monitor /></el-icon>
            <template #title>监测项目</template>
          </el-menu-item>

          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>Settings</template>
          </el-menu-item>
        </el-menu>

        <!-- User Info Section -->
        <div class="sidebar-user-section">
          <div class="user-info-content">
            <el-icon :size="20" color="#64748b"><User /></el-icon>
            <template v-if="!isCollapsed">
              <span class="user-name">{{ sidebarUsername }}</span>
              <el-tag size="small" type="info" effect="plain" style="margin-left: auto;">用户</el-tag>
            </template>
          </div>
          <el-button
            v-if="!isCollapsed"
            text
            type="danger"
            size="small"
            style="width: 100%; margin-top: 8px;"
            @click="handleLogout"
          >
            退出登录
          </el-button>
          <el-button
            v-else
            text
            type="danger"
            size="small"
            :icon="SwitchButton"
            style="width: 100%; margin-top: 8px;"
            @click="handleLogout"
          />
        </div>
      </el-aside>
      
      <!-- Main Content Container with Rounded Corner -->
      <el-container class="main-content-container">

        
        <el-main>
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Odometer, TrendCharts, DataAnalysis, Monitor, Setting, User, Fold, Expand, SwitchButton } from '@element-plus/icons-vue'

const router = useRouter()
const isCollapsed = ref(false)

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
.h-screen {
  height: 100vh;
}
.bg-base {
  background-color: var(--color-bg-base);
}

.glass-sidebar {
  background: transparent; /* Sidebar is just on the white base */
  /* Remove border-right to avoid hard line */
  display: flex;
  flex-direction: column;
}

.logo-area {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 12px;
}

.collapse-btn {
  padding: 4px;
  color: #94a3b8;
}

.sidebar-user-section {
  margin-top: auto;
  padding: 12px 16px;
  border-top: 1px solid #e5e7eb;
}

.user-info-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 14px;
  color: #475569;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.glass-header {
  background: transparent; /* Transparent header */
  /* Remove border to blend with main content */
  height: 64px;
}

.custom-menu {
  border-right: none;
  padding: 1rem 0;
  flex: 1;
}

:deep(.el-menu--collapse) {
  width: 100%;
}

:deep(.el-menu-item) {
  border-radius: var(--radius-lg);
  margin: 4px 12px;
  height: 48px;
}

:deep(.el-menu-item.is-active) {
  background-color: var(--color-primary-light);
  font-weight: 500;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(99, 102, 241, 0.05);
}

.main-content-container {
  background-color: #f3f4f6;
  border-radius: var(--radius-2xl);
  overflow: hidden; /* This might be cutting off the button, but 'auto' is better for main content scrolling */
  overflow-y: auto;
  margin: 16px; /* Uniform margin */
  box-shadow: -4px 0 20px rgba(0,0,0,0.03);
  position: relative; /* Ensure child absolute positioning relates to this */
}

/* Fix for back-to-top button if it exists in Element Plus components */
:deep(.el-backtop) {
  position: absolute;
  bottom: 40px;
  right: 40px;
  z-index: 100;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
