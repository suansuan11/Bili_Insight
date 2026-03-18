import axios from 'axios'
import router from '@/router'

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
            // 只有在非登录/注册页面才自动跳转，避免登录失败时死循环
            const path = window.location.pathname
            if (path !== '/login' && path !== '/register') {
                localStorage.removeItem('token')
                router.push('/login')
            }
        }
        return Promise.reject(error)
    }
)

export default service
