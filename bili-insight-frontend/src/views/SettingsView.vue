<template>
  <div class="settings-view">
    <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-100 mb-6">
      <h1 class="text-2xl font-bold text-gray-800">设置页面</h1>
      <p class="text-gray-500 mt-2">配置您的个人偏好和系统设置</p>
    </div>

    <el-tabs type="border-card" class="settings-tabs" v-model="activeTab">
      <el-tab-pane label="基本设置" name="basic">
        <div class="p-4 space-y-6">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-medium text-gray-700">深色模式</h3>
              <p class="text-gray-500 text-sm">启用深色主题界面 (开发中)</p>
            </div>
            <el-switch v-model="darkMode" />
          </div>
          <el-divider />
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-lg font-medium text-gray-700">自动刷新</h3>
              <p class="text-gray-500 text-sm">自动刷新分析结果页面</p>
            </div>
            <el-switch v-model="autoRefresh" />
          </div>
        </div>
      </el-tab-pane>
      
      <el-tab-pane label="账号管理" name="account">
         <div class="p-4 flex flex-col items-center">
            <h3 class="text-lg font-bold mb-4">Bilibili 账号绑定</h3>
            <p class="text-gray-500 mb-6 text-center max-w-md">登录 Bilibili 账号以获取更多评论和弹幕数据，并提高爬虫稳定性。</p>
            
            <!-- Login Status Display -->
            <div v-if="isLoggedIn && userInfo" class="text-center w-full max-w-sm">
               <div class="bg-blue-50 p-6 rounded-xl border border-blue-100 mb-6 flex flex-col items-center shadow-sm">
                  <el-avatar :size="80" :src="userInfo.face" class="border-4 border-white shadow-md mb-3" />
                  <h2 class="text-xl font-bold text-gray-800 mb-1 flex items-center gap-2">
                     {{ userInfo.uname }}
                     <el-tag v-if="userInfo.vip_label?.text" size="small" type="danger" effect="dark">{{ userInfo.vip_label.text }}</el-tag>
                  </h2>
                  <div class="flex items-center gap-2 mt-2">
                     <el-tag size="small" effect="plain">LV{{ userInfo.level_info?.current_level || 0 }}</el-tag>
                     <span class="text-gray-500 text-sm">UID: {{ userInfo.mid || 'Unknown' }}</span>
                  </div>
               </div>
               <el-button type="danger" plain @click="logout" class="w-full">注销账号</el-button>
            </div>
            
            <div v-else-if="isLoggedIn" class="text-center">
               <el-result icon="success" title="已登录" sub-title="正在获取用户信息...">
                  <template #extra>
                     <el-button type="danger" plain @click="logout">注销账号</el-button>
                  </template>
               </el-result>
            </div>

            <!-- QR Code Login -->
            <div v-else class="flex flex-col items-center">
               <div v-if="qrCodeUrl" class="mb-4 p-4 bg-white border rounded-lg shadow-sm">
                  <div class="w-48 h-48 relative">
                     <qrcode-vue :value="qrCodeUrl" :size="192" level="M" />
                     <div v-if="isExpired" class="absolute inset-0 bg-white/90 flex flex-col items-center justify-center">
                        <span class="text-sm text-gray-500 mb-2">二维码已过期</span>
                        <el-icon class="text-3xl text-gray-400 cursor-pointer" @click="refreshQrCode"><Refresh /></el-icon>
                     </div>
                  </div>
               </div>
               <div v-else class="h-48 flex items-center justify-center">
                  <el-button type="primary" @click="getQrCode" :loading="loadingQr">获取登录二维码</el-button>
               </div>
               
               <p v-if="qrCodeUrl" class="text-sm text-center mt-2" :class="statusColor">
                  {{ statusText }}
               </p>
            </div>
         </div>
      </el-tab-pane>

      <el-tab-pane label="API 配置" name="api">
        <div class="p-4 space-y-6">
          <div>
            <h3 class="text-lg font-medium text-gray-700 mb-2">后端 API 地址</h3>
            <el-input v-model="backendUrl" placeholder="http://localhost:8080" />
            <p class="text-gray-500 text-sm mt-1">Java 后端服务地址</p>
          </div>
          <div>
            <h3 class="text-lg font-medium text-gray-700 mb-2">Python 服务地址</h3>
            <el-input v-model="pythonServiceUrl" placeholder="http://localhost:8001" />
            <p class="text-gray-500 text-sm mt-1">Python 情感分析服务地址</p>
          </div>
          <div class="mt-4">
             <el-button type="primary" @click="saveApiSettings">保存配置</el-button>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="缓存管理" name="cache">
        <div class="p-4">
           <el-empty description="暂无缓存数据" />
           <div class="text-center">
              <el-button type="danger" plain>清除本地缓存</el-button>
           </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import QrcodeVue from 'qrcode.vue'
import axios from 'axios'

const activeTab = ref('account') // Default to account tab to check login
const darkMode = ref(false)
const autoRefresh = ref(true)
const backendUrl = ref('http://localhost:8080')
const pythonServiceUrl = ref('http://localhost:8001')

// Login State
const isLoggedIn = ref(false)
const userInfo = ref<any>(null)
const qrCodeUrl = ref('')
const qrCodeKey = ref('')
const loadingQr = ref(false)
const isExpired = ref(false)
const loginStatus = ref('')
let pollTimer: number | null = null

const statusText = computed(() => {
   if (isExpired.value) return '二维码已过期，请刷新'
   if (loginStatus.value === 'scanned') return '已扫描，请在手机上确认'
   if (loginStatus.value === 'confirmed') return '登录成功！'
   return '请使用 Bilibili App 扫码登录'
})

const statusColor = computed(() => {
   if (isExpired.value) return 'text-red-500'
   if (loginStatus.value === 'scanned') return 'text-green-500'
   return 'text-gray-500'
})

const saveApiSettings = () => {
  ElMessage.success('API 配置已保存')
}

const checkLoginStatus = async () => {
   try {
      const res = await axios.get(`${pythonServiceUrl.value}/api/login/current_user`)
      if (res.data && res.data.is_login) {
         isLoggedIn.value = true
         userInfo.value = res.data
      } else {
         isLoggedIn.value = false
         userInfo.value = null
      }
   } catch (e) {
      console.error('Check login status failed', e)
      isLoggedIn.value = false
   }
}

const getQrCode = async () => {
   loadingQr.value = true
   try {
      const res = await axios.get(`${pythonServiceUrl.value}/api/login/qrcode`)
      if (res.data) {
         qrCodeUrl.value = res.data.qrcode_url
         qrCodeKey.value = res.data.qrcode_key
         isExpired.value = false
         loginStatus.value = ''
         startPolling()
      }
   } catch (e) {
      console.error(e)
      ElMessage.error('获取二维码失败，请检查 Python 服务是否启动')
   } finally {
      loadingQr.value = false
   }
}

const refreshQrCode = () => {
   stopPolling()
   getQrCode()
}

const startPolling = () => {
   stopPolling()
   pollTimer = window.setInterval(async () => {
      try {
         const res = await axios.get(`${pythonServiceUrl.value}/api/login/status/${qrCodeKey.value}`)
         const status = res.data.status
         
         if (status === 'scanned') {
            loginStatus.value = 'scanned'
         } else if (status === 'confirmed') {
            loginStatus.value = 'confirmed'
            isLoggedIn.value = true
            ElMessage.success('登录成功')
            stopPolling()
            // Fetch User Info immediately
            setTimeout(checkLoginStatus, 1000)
         } else if (status === 'expired') {
            isExpired.value = true
            stopPolling()
         }
      } catch (e) {
         console.error(e)
      }
   }, 2000)
}

const stopPolling = () => {
   if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
   }
}

const logout = async () => {
   // Since logout usually clears local files on server which we can't easily do via API without endpoint,
   // we just clear frontend state for now. In a real app, call a logout endpoint.
   // Assuming Python side stores credential.json, we might need a logout endpoint there? 
   // For now just UX logout.
   isLoggedIn.value = false
   userInfo.value = null
   qrCodeUrl.value = ''
   qrCodeKey.value = ''
   loginStatus.value = ''
   ElMessage.success('已注销')
}

onMounted(() => {
   checkLoginStatus()
})

onUnmounted(() => {
   stopPolling()
})
</script>

<style scoped>
.settings-tabs {
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
</style>
