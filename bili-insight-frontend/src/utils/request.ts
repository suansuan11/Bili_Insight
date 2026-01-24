import axios from 'axios'

// Create an axios instance
const service = axios.create({
    baseURL: '/', // Use proxy in development
    timeout: 60000 // Request timeout
})

// Request interceptor
service.interceptors.request.use(
    config => {
        // do something before request is sent
        return config
    },
    error => {
        // do something with request error
        console.log(error) // for debug
        return Promise.reject(error)
    }
)

// Response interceptor
service.interceptors.response.use(
    response => {
        const res = response.data
        // You can add custom error handling here based on your backend response structure
        return res
    },
    error => {
        console.log('err' + error) // for debug
        return Promise.reject(error)
    }
)

export default service
