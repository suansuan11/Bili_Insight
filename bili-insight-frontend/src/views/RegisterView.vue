<template>
  <div class="register-page">
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

    <!-- Right: Register Form -->
    <div class="form-panel">
      <div class="form-wrapper">
        <div class="form-header">
          <h2>创建账户</h2>
          <p class="form-subtitle">注册以开始使用舆情分析服务</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          size="large"
          @submit.prevent="handleRegister"
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

          <el-form-item label="邮箱（可选）" prop="email">
            <el-input
              v-model="form.email"
              placeholder="请输入邮箱"
              prefix-icon="Message"
              clearable
            />
          </el-form-item>

          <el-form-item label="选择角色" prop="role">
            <div class="role-cards">
              <div
                class="role-card"
                :class="{ active: form.role === 'CREATOR' }"
                @click="form.role = 'CREATOR'"
              >
                <el-icon :size="32" class="role-card-icon"><VideoPlay /></el-icon>
                <div class="role-card-title">内容创作者</div>
                <div class="role-card-desc">UP主 / MCN机构</div>
              </div>

              <div
                class="role-card"
                :class="{ active: form.role === 'BRAND' }"
                @click="form.role = 'BRAND'"
              >
                <el-icon :size="32" class="role-card-icon"><OfficeBuilding /></el-icon>
                <div class="role-card-title">品牌方</div>
                <div class="role-card-desc">企业 / 市场部门</div>
              </div>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              native-type="submit"
              :loading="loading"
              class="submit-btn"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>

        <div class="form-footer">
          <span class="footer-text">已有账号？</span>
          <router-link to="/login" class="footer-link">立即登录</router-link>
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
import {
  TrendCharts,
  DataAnalysis,
  Monitor,
  VideoPlay,
  OfficeBuilding,
} from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  email: '',
  role: 'CREATOR',
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
  email: [
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await request.post('/insight/auth/register', form)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error: any) {
    const msg = error.response?.data || error.message || '注册失败'
    ElMessage.error(typeof msg === 'string' ? msg : '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* ===== Left Showcase Panel ===== */
.showcase-panel {
  position: relative;
  width: 55%;
  background: linear-gradient(160deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
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
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00d2ff;
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
  background: radial-gradient(circle, rgba(0, 210, 255, 0.08) 0%, transparent 70%);
}

.circle-2 {
  width: 300px;
  height: 300px;
  bottom: -60px;
  left: -60px;
  background: radial-gradient(circle, rgba(118, 75, 162, 0.12) 0%, transparent 70%);
}

.circle-3 {
  width: 200px;
  height: 200px;
  top: 50%;
  right: 10%;
  background: radial-gradient(circle, rgba(0, 210, 255, 0.05) 0%, transparent 70%);
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
  overflow-y: auto;
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
}

.form-header {
  margin-bottom: 32px;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a2e;
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

/* ===== Role Selection Cards ===== */
.role-cards {
  display: flex;
  gap: 16px;
  width: 100%;
}

.role-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 12px;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s ease;
  background: #fafafa;
}

.role-card:hover {
  border-color: #b3d8ff;
  background: #f0f7ff;
}

.role-card.active {
  border-color: #409eff;
  background: #ecf5ff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.12);
}

.role-card-icon {
  color: #909399;
  margin-bottom: 10px;
  transition: color 0.25s ease;
}

.role-card.active .role-card-icon {
  color: #409eff;
}

.role-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.role-card-desc {
  font-size: 12px;
  color: #909399;
}

.role-card.active .role-card-title {
  color: #409eff;
}

/* ===== Submit & Footer ===== */
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
  .register-page {
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
