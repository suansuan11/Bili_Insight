import axios from 'axios'
import router from '@/router'
import { ElMessage } from 'element-plus'

const service = axios.create({
    baseURL: '/',
    timeout: 60000
})

service.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token')
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`
        }
        return config
    },
    error => {
        console.error('Request error:', error)
        return Promise.reject(error)
    }
)

service.interceptors.response.use(
    response => {
        return response.data
    },
    error => {
        if (error.response && error.response.status === 401) {
            const path = window.location.pathname
            if (path !== '/login' && path !== '/register') {
                localStorage.removeItem('token')
                localStorage.removeItem('user')
                ElMessage.warning('登录已过期，请重新登录')
                router.push('/login')
            }
        }
        return Promise.reject(error)
    }
)

export default service
