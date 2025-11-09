import axios from 'axios'

// Use relative URL for production (nginx will proxy to backend)
// Fall back to VITE_API_URL for local development
const API_BASE = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:5000')

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 minutes for video processing
})

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

