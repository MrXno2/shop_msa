import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const isAdminPage = window.location.pathname.startsWith('/admin')
      if (isAdminPage) {
        window.location.href = '/admin/login'
      } else {
        window.location.href = '/auth'
      }
    }
    return Promise.reject(error)
  },
)

export default apiClient
