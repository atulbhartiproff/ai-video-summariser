import axios from 'axios'

// Use relative URL for production (nginx will proxy to backend)
// Only use absolute URL for local development with Vite dev server
// In production (Docker/ECS), always use relative URLs so nginx can proxy
const isDevelopment = import.meta.env.DEV
const API_BASE = isDevelopment 
  ? (import.meta.env.VITE_API_URL || 'http://localhost:5000')
  : '' // Empty string = relative URLs (nginx will proxy)

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 minutes for video processing
})

// Debug log (remove in production if needed)
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE || '(relative - will use nginx proxy)')
}

/**
 * Upload video file and get summary
 * @param {File} file - Video file to upload
 * @param {Function} onProgress - Progress callback (progress: 0-100)
 * @returns {Promise<Object>} Summary data
 */
export const uploadVideo = async (file, onProgress) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        )
        onProgress(percentCompleted)
      }
    },
  })

  return response.data
}

/**
 * Check backend health
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  const response = await api.get('/health')
  return response.data
}

