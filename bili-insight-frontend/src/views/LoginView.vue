<template>
  <div class="login-page">
    <!-- Left: Product Showcase -->
    <div class="showcase-panel">
      <div class="showcase-content">
        <div class="brand">
          <h1 class="brand-name">Bili-Insight</h1>
          <p class="brand-tagline">B站智能舆情分析平台</p>
        </div>

        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <el-icon :size="28"><TrendCharts /></el-icon>
            </div>
            <div class="feature-text">
              <h3>情绪时间轴</h3>
              <p>精确到秒的视频舆情追踪</p>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">
              <el-icon :size="28"><DataAnalysis /></el-icon>
            </div>
            <div class="feature-text">
              <h3>切面分析</h3>
              <p>多维度口碑量化评估</p>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">
              <el-icon :size="28"><Monitor /></el-icon>
            </div>
            <div class="feature-text">
              <h3>自动监测</h3>
              <p>品牌舆情实时预警</p>
            </div>
          </div>
        </div>
      </div>

      <div class="showcase-decoration">
        <div class="circle circle-1"></div>
        <div class="circle circle-2"></div>
        <div class="circle circle-3"></div>
      </div>
    </div>

    <!-- Right: Login Form -->
    <div class="form-panel">
      <div class="form-wrapper">
        <div class="form-header">
          <h2>欢迎回来</h2>
          <p class="form-subtitle">登录您的账户</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          @submit.prevent="handleLogin"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              clearable
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              native-type="submit"
              :loading="loading"
              class="submit-btn"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>

        <div class="form-footer">
          <span class="footer-text">还没有账号？</span>
          <router-link to="/register" class="footer-link">立即注册</router-link>
        </div>
      </div>

      <div class="copyright">&copy; 2026 Bili-Insight</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { TrendCharts, DataAnalysis, Monitor } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名至少3个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res: any = await request.post('/insight/auth/login', form)
    const token = res.token || res.data?.token
    if (token) {
      localStorage.setItem('token', token)
      // 缓存用户基本信息，避免每次都请求 /me
      localStorage.setItem('userId', String(res.userId ?? ''))
      localStorage.setItem('username', res.username ?? form.username)
      localStorage.setItem('role', res.role ?? '')
      ElMessage.success('登录成功')
      router.push('/')
    } else {
      ElMessage.error(res.message || '登录失败')
    }
  } catch (error: any) {
    const data = error.response?.data
    let msg = '用户名或密码错误'
    if (typeof data === 'string' && data.length < 100) {
      msg = data
    } else if (data?.message) {
      msg = data.message
    } else if (error.message?.includes('Network')) {
      msg = '无法连接到服务器，请检查后端是否启动'
    }
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* ===== Left Showcase Panel ===== */
.showcase-panel {
  position: relative;
  width: 55%;
  background: #0f172a;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.showcase-content {
  position: relative;
  z-index: 2;
  padding: 60px;
  max-width: 520px;
}

.brand {
  margin-bottom: 64px;
}

.brand-name {
  font-size: 42px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 2px;
  margin: 0 0 12px 0;
}

.brand-tagline {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  letter-spacing: 4px;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 36px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.feature-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #60a5fa;
}

.feature-text h3 {
  margin: 0 0 6px 0;
  font-size: 17px;
  font-weight: 600;
  color: #ffffff;
}

.feature-text p {
  margin: 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
}

/* Decorative circles */
.showcase-decoration {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.circle {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.circle-1 {
  width: 400px;
  height: 400px;
  top: -100px;
  right: -80px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.12) 0%, transparent 70%);
}

.circle-2 {
  width: 300px;
  height: 300px;
  bottom: -60px;
  left: -60px;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
}

.circle-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  right: 10%;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.07) 0%, transparent 70%);
}

/* ===== Right Form Panel ===== */
.form-panel {
  width: 45%;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  position: relative;
}

.form-wrapper {
  width: 100%;
  max-width: 380px;
}

.form-header {
  margin-bottom: 40px;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.form-subtitle {
  font-size: 15px;
  color: #909399;
  margin: 0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  padding: 4px 12px;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #409eff inset;
}

.submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  letter-spacing: 2px;
}

.form-footer {
  text-align: center;
  margin-top: 24px;
}

.footer-text {
  font-size: 14px;
  color: #909399;
}

.footer-link {
  font-size: 14px;
  color: #409eff;
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}

.footer-link:hover {
  text-decoration: underline;
}

.copyright {
  position: absolute;
  bottom: 24px;
  font-size: 13px;
  color: #c0c4cc;
}

/* ===== Responsive ===== */
@media (max-width: 900px) {
  .login-page {
    flex-direction: column;
  }

  .showcase-panel {
    width: 100%;
    height: auto;
    min-height: 260px;
    padding: 40px 24px;
  }

  .showcase-content {
    padding: 0;
  }

  .brand {
    margin-bottom: 24px;
  }

  .brand-name {
    font-size: 28px;
  }

  .features {
    gap: 16px;
  }

  .form-panel {
    width: 100%;
    flex: 1;
    padding: 32px 24px;
  }
}
</style>
