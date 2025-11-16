import axios from 'axios'

const baseURL = import.meta?.env?.VITE_API_URL || 'https://unequally-paternal-guan.cloudpub.ru/'

export const api = axios.create({
  baseURL,
  withCredentials: false
})

// Перехватчик запросов для автоматической установки токена
api.interceptors.request.use(
  (config) => {
    // Проверяем токен из localStorage перед каждым запросом
    const token = localStorage.getItem('dream_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Перехватчик ответов для обработки 401 ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Очищаем токен при 401 ошибке
      localStorage.removeItem('dream_token')
      localStorage.removeItem('dream_user')
      delete api.defaults.headers.common.Authorization
    }
    return Promise.reject(error)
  }
)

export const setAuthToken = (token) => {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`
    localStorage.setItem('dream_token', token)
  } else {
    delete api.defaults.headers.common.Authorization
    localStorage.removeItem('dream_token')
  }
}
