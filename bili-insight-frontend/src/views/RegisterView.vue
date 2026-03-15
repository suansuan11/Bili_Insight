<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2>Register</h2>
      <el-form :model="form" @submit.prevent="handleRegister">
        <el-form-item label="Username">
          <el-input v-model="form.username" required></el-input>
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="form.password" type="password" required></el-input>
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading">Register</el-button>
        <div class="links">
          <router-link to="/login">Already have an account? Login</router-link>
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

const handleRegister = async () => {
  loading.value = true
  try {
    const res: any = await request.post('/insight/auth/register', form.value)
    if (res.code === 0 && res.data?.token) {
      localStorage.setItem('token', res.data.token)
      ElMessage.success('Registration successful')
      router.push('/')
    } else {
      ElMessage.error(res.message || 'Registration failed')
    }
  } catch (error: any) {
    ElMessage.error(error.message || 'Registration failed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}
.register-card {
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
