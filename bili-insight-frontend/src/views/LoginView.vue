<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>Login</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item label="Username">
          <el-input v-model="form.username" required></el-input>
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="form.password" type="password" required></el-input>
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading">Login</el-button>
        <div class="links">
          <router-link to="/register">Don't have an account? Register</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const router = useRouter()
const form = ref({ username: '', password: '' })
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    const res: any = await request.post('/insight/auth/login', form.value)
    if (res.code === 0 && res.data?.token) {
      localStorage.setItem('token', res.data.token)
      ElMessage.success('Login successful')
      router.push('/')
    } else {
      ElMessage.error(res.message || 'Login failed')
    }
  } catch (error: any) {
    ElMessage.error(error.message || 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}
.login-card {
  width: 400px;
  padding: 20px;
}
h2 {
  text-align: center;
  margin-bottom: 20px;
}
.links {
  margin-top: 15px;
  text-align: center;
}
</style>
