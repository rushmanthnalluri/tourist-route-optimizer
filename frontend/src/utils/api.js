import axios from 'axios'
import axiosRetry from 'axios-retry'

const BASE = import.meta.env.VITE_API_BASE ?? ''

const apiClient = axios.create({
  baseURL: BASE,
  timeout: 900000,
  headers: {
    'Content-Type': 'application/json'
  }
})

axiosRetry(apiClient, { 
  retries: 3, 
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) || error.response?.status === 429
  }
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Request failed:', error)
    if (error.response) {
      
      const { data, status } = error.response
      throw new Error(data?.message || `API Error ${status}`)
    } else if (error.request) {
      
      throw new Error('Network error or request timeout')
    } else {
      
      throw new Error(error.message)
    }
  }
)

export const api = {
  
  getAttractions: () => apiClient.get(`/api/attractions`).then(r => r.data),
  getGraph:       () => apiClient.get(`/api/graph`).then(r => r.data),

  runSearch: (payload) => apiClient.post(`/api/search/run`, payload).then(r => r.data),
  compareSearch: (payload) => apiClient.post(`/api/search/compare`, payload).then(r => r.data),

  scheduleCSP: (payload) => apiClient.post(`/api/csp/schedule`, payload).then(r => r.data),

  computeUtility: (payload)  => apiClient.post(`/api/decision/utility`, payload).then(r => r.data),
  runMinimax:     (payload)  => apiClient.post(`/api/decision/minimax`, payload).then(r => r.data),
  expectedUtility:(payload)  => apiClient.post(`/api/decision/expected-utility`, payload).then(r => r.data),

  bayesUpdate:    (payload)  => apiClient.post(`/api/probabilistic/bayes-update`, payload).then(r => r.data),
  infer:          (payload)  => apiClient.post(`/api/probabilistic/infer`, payload).then(r => r.data),
  hmmTrack:       (payload)  => apiClient.post(`/api/probabilistic/hmm`, payload).then(r => r.data),
  getLiveWeather: ()         => apiClient.get(`/api/probabilistic/live-weather`).then(r => r.data),

  hybridPlan: (payload) => apiClient.post(`/api/hybrid/plan`, payload).then(r => r.data),
}
