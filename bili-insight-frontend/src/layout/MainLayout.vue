<template>
  <div class="app-container">
    <el-container class="h-screen" style="background: #ffffff;">
      <!-- Sidebar -->
      <el-aside width="240px" class="glass-sidebar">
        <div class="logo-area">
          <h1 class="text-xl font-bold bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent" 
              style="background: linear-gradient(to right, #6366f1, #8b5cf6); -webkit-background-clip: text; background-clip: text; color: transparent;">
            Bili Insight
          </h1>
        </div>
        
        <el-menu
          router
          :default-active="$route.path"
          class="custom-menu"
          background-color="transparent"
          text-color="#64748b"
          active-text-color="#6366f1"
        >
          <el-menu-item index="/">
            <el-icon><Odometer /></el-icon>
            <span>Dashboard</span>
          </el-menu-item>
          
          <el-menu-item index="/popular">
            <el-icon><TrendCharts /></el-icon>
            <span>Popular Videos</span>
          </el-menu-item>
          
          <el-menu-item index="/analysis">
            <el-icon><DataAnalysis /></el-icon>
            <span>Analysis</span>
          </el-menu-item>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>Settings</span>
          </el-menu-item>
        </el-menu>
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
import { Odometer, TrendCharts, DataAnalysis, Setting } from '@element-plus/icons-vue'
// Note: Icons need to be registered globally or imported here. 
// Assuming global registration or I will register them in main.ts if needed.
// Ideally usage in script setup is enough if auto-imported, but let's be safe.
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
  /* Remove border-bottom for cleaner look */
}

.glass-header {
  background: transparent; /* Transparent header */
  /* Remove border to blend with main content */
  height: 64px;
}

.custom-menu {
  border-right: none;
  padding: 1rem 0;
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
  background-color: #f3f4f6; /* Gray-100 for better contrast against white sidebar */
  border-radius: var(--radius-2xl); /* Round all corners for consistent floating card look */
  overflow: hidden;
  margin: 16px 16px 16px 0; /* Increased margin for better floating effect */
  box-shadow: -4px 0 20px rgba(0,0,0,0.03);
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
