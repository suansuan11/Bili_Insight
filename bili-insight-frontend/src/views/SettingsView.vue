<template>
  <div class="settings-view">
    <div class="settings-header">
      <h1 class="settings-title">系统设置</h1>
      <p class="settings-subtitle">配置个人偏好、账号绑定和系统参数</p>
    </div>

    <el-tabs class="settings-tabs" v-model="activeTab">
      <el-tab-pane label="基本设置" name="basic">
        <div class="tab-content">
          <div class="setting-row">
            <div>
              <h3 class="setting-name">深色模式</h3>
              <p class="setting-desc">启用深色主题界面</p>
            </div>
            <el-switch :model-value="isDark" @click="(e: MouseEvent) => toggleDark(e)" />
          </div>
          <el-divider />
          <div class="setting-row">
            <div>
              <h3 class="setting-name">自动刷新</h3>
              <p class="setting-desc">自动刷新分析结果页面</p>
            </div>
            <el-switch v-model="autoRefresh" />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="账号绑定" name="account">
        <div class="tab-content account-tab">
          <h3 class="account-title">Bilibili 账号绑定</h3>
          <p class="account-desc">登录 Bilibili 账号以获取更多评论和弹幕数据，并提高爬虫稳定性。</p>

          <!-- Logged in state -->
          <div v-if="isLoggedIn && userInfo && userInfo.is_login !== false" class="logged-in-card">
            <div class="user-profile">
              <!-- B站头像有防盗链，通过后端代理转发 -->
              <el-avatar
                :size="72"
                :src="userInfo.face ? `/insight/login/qrcode/image-proxy?url=${encodeURIComponent(userInfo.face)}` : ''"
                class="user-avatar"
              />
              <div class="user-details">
                <h2 class="bili-username">
                  {{ userInfo.uname || '未知用户' }}
                  <el-tag v-if="userInfo.vip_label?.text" size="small" type="danger" effect="dark">
                    {{ userInfo.vip_label.text }}
                  </el-tag>
                </h2>
                <div class="user-tags">
                  <el-tag size="small" effect="plain">LV{{ userInfo.level_info?.current_level ?? 0 }}</el-tag>
                  <span class="uid-text">UID: {{ userInfo.mid ?? '—' }}</span>
                </div>
              </div>
            </div>
            <el-button type="danger" plain @click="logout" style="width: 100%; margin-top: 16px;">注销账号</el-button>
          </div>

          <div v-else-if="isLoggedIn" class="text-center">
            <el-result icon="success" title="已登录" sub-title="正在获取用户信息...">
              <template #extra>
                <el-button type="danger" plain @click="logout">注销账号</el-button>
              </template>
            </el-result>
          </div>

          <!-- QR Code Login -->
          <div v-else class="qr-section">
            <div v-if="qrCodeUrl" class="qr-wrapper">
              <div class="qr-box">
                <qrcode-vue :value="qrCodeUrl" :size="192" level="M" />
                <div v-if="isExpired" class="qr-expired-overlay">
                  <span class="qr-expired-text">二维码已过期</span>
                  <el-icon class="qr-refresh-icon" @click="refreshQrCode"><Refresh /></el-icon>
                </div>
              </div>
            </div>
            <div v-else class="qr-placeholder">
              <el-button type="primary" @click="getQrCode" :loading="loadingQr">获取登录二维码</el-button>
            </div>
            <p v-if="qrCodeUrl" class="qr-status" :class="statusClass">{{ statusText }}</p>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="API 配置" name="api">
        <div class="tab-content">
          <div class="api-form">
            <div class="api-field">
              <label class="api-label">后端 API 地址</label>
              <el-input v-model="backendUrl" placeholder="http://localhost:8080" />
              <p class="api-hint">Java Spring Boot 后端服务地址</p>
            </div>
            <div class="api-field">
              <label class="api-label">Python 服务地址</label>
              <el-input v-model="pythonServiceUrl" placeholder="http://localhost:8001" />
              <p class="api-hint">Python FastAPI 情感分析服务地址</p>
            </div>
            <el-button type="primary" @click="saveApiSettings">保存配置</el-button>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="缓存管理" name="cache">
        <div class="tab-content">
          <el-empty description="暂无缓存数据" />
          <div style="text-align: center; margin-top: 12px;">
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
import request from '@/utils/request'
import { useDarkMode } from '@/composables/useDarkMode'

const { isDark, toggleDark } = useDarkMode()

const activeTab = ref('account')
const autoRefresh = ref(true)
const backendUrl = ref('http://localhost:8080')
const pythonServiceUrl = ref('http://localhost:8001')

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

const statusClass = computed(() => {
  if (isExpired.value) return 'status-error'
  if (loginStatus.value === 'scanned') return 'status-success'
  return 'status-default'
})

const saveApiSettings = () => {
  ElMessage.success('API 配置已保存')
}

const checkLoginStatus = async () => {
  try {
    const res: any = await request.get('/insight/auth/me')
    if (res.biliLinked) {
      isLoggedIn.value = true
      try {
        const biliRes: any = await request.get('/insight/login/current_user')
        if (biliRes && biliRes.is_login !== false) {
          userInfo.value = biliRes
        } else {
          // sessdata 已失效，提示用户重新绑定
          isLoggedIn.value = false
          userInfo.value = null
          ElMessage.warning('B站账号凭证已过期，请重新扫码绑定')
        }
      } catch {
        userInfo.value = { uname: '已登录', is_login: true }
      }
    } else {
      isLoggedIn.value = false
      userInfo.value = null
    }
  } catch (e) {
    isLoggedIn.value = false
  }
}

const getQrCode = async () => {
  loadingQr.value = true
  try {
    const res: any = await request.get('/insight/login/qrcode/generate')
    // axios 拦截器已解包 response.data，res 本身就是 { qrcode_url, qrcode_key }
    const url = res.qrcode_url ?? res.data?.qrcode_url
    const key = res.qrcode_key ?? res.data?.qrcode_key
    if (url && key) {
      qrCodeUrl.value = url
      qrCodeKey.value = key
      isExpired.value = false
      loginStatus.value = ''
      startPolling()
    } else {
      ElMessage.error('获取二维码失败，返回数据异常')
    }
  } catch (e) {
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
      const res: any = await request.get(`/insight/login/qrcode/poll?key=${qrCodeKey.value}`)
      // axios 拦截器已解包，res 本身就是 JSON 对象
      const status = res.status ?? res.data?.status
      if (status === 'scanned') {
        loginStatus.value = 'scanned'
      } else if (status === 'confirmed') {
        loginStatus.value = 'confirmed'
        isLoggedIn.value = true
        ElMessage.success('登录成功')
        stopPolling()
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
  try {
    await request.post('/insight/login/logout')
  } catch (e) {
    console.error('注销请求失败', e)
  }
  isLoggedIn.value = false
  userInfo.value = null
  qrCodeUrl.value = ''
  qrCodeKey.value = ''
  loginStatus.value = ''
  ElMessage.success('已注销 B站账号绑定')
}

onMounted(() => {
  checkLoginStatus()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.settings-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-header {
  margin-bottom: 4px;
}

.settings-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0 0 4px 0;
}

.settings-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.settings-tabs {
  background: #fff;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

:deep(.el-tabs__header) {
  margin: 0;
  padding: 0 16px;
  border-bottom: 1px solid var(--color-border);
  background: #fafbfc;
}

:deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  height: 48px;
  line-height: 48px;
}

:deep(.el-tabs__item.is-active) {
  color: #2563eb;
}

:deep(.el-tabs__active-bar) {
  background: #2563eb;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

/* Tab Content */
.tab-content {
  padding: 24px;
}

/* Basic Settings */
.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.setting-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--color-text-main);
  margin: 0 0 4px 0;
}

.setting-desc {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* Account Tab */
.account-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.account-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0 0 8px 0;
}

.account-desc {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0 0 24px 0;
  max-width: 440px;
}

.logged-in-card {
  width: 100%;
  max-width: 360px;
  background: #f8fafc;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}

.bili-username {
  font-size: 17px;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.uid-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* QR Code */
.qr-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.qr-wrapper {
  padding: 16px;
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.qr-box {
  width: 192px;
  height: 192px;
  position: relative;
}

.qr-expired-overlay {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.qr-expired-text {
  font-size: 13px;
  color: #64748b;
}

.qr-refresh-icon {
  font-size: 28px;
  color: #94a3b8;
  cursor: pointer;
  transition: color 0.15s;
}

.qr-refresh-icon:hover {
  color: #2563eb;
}

.qr-placeholder {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-status {
  font-size: 13px;
  margin: 0;
}

.status-default { color: #64748b; }
.status-success { color: #16a34a; font-weight: 500; }
.status-error   { color: #dc2626; }

/* API Form */
.api-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 480px;
}

.api-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.api-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-main);
}

.api-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
}
</style>
