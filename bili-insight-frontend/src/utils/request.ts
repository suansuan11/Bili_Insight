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
        console.log(error)
        return Promise.reject(error)
    }
)

service.interceptors.response.use(
    response => {
        const res = response.data
        return res
    },
    error => {
        console.log('err' + error)
        if (error.response && error.response.status === 401) {
            router.push('/login')
        }
        return Promise.reject(error)
    }
)

export default service
