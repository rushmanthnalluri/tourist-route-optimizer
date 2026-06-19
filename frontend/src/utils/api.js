import axios from 'axios'
import axiosRetry from 'axios-retry'

const BASE = import.meta.env.VITE_API_BASE ?? ''
const TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '900000', 10)

const apiClient = axios.create({
  baseURL: BASE,
  timeout: TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
})

axiosRetry(apiClient, { 
  retries: 3, 
  retryDelay: axiosRetry.exponentialDelay,
  retryCondition: (error) => {
    // Only retry GET requests (idempotent). Never retry POSTs —
    // they trigger expensive algorithm runs and retrying compounds server load.
    const method = error.config?.method?.toLowerCase()
    if (method !== 'get') return false
    return axiosRetry.isNetworkOrIdempotentRequestError(error) || error.response?.status === 429
  }
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Request failed:', error)
    if (error.response) {
      
      // FastAPI uses 'detail' for validation errors, 'message' for custom errors
      const { data, status } = error.response
      const msg = data?.detail || data?.message || `API Error ${status}`
      throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
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
  fetchLiveTraffic: () => apiClient.get(`/api/search/live-traffic`).then(r => r.data),

  scheduleCSP: (payload) => apiClient.post(`/api/csp/schedule`, payload).then(r => r.data),

  computeUtility: (payload)  => apiClient.post(`/api/decision/utility`, payload).then(r => r.data),
  runMinimax:     (payload)  => apiClient.post(`/api/decision/minimax`, payload).then(r => r.data),
  expectedUtility:(payload)  => apiClient.post(`/api/decision/expected-utility`, payload).then(r => r.data),
  negotiate:      (payload)  => apiClient.post(`/api/decision/negotiate`, payload).then(r => r.data),

  bayesUpdate:    (payload)  => apiClient.post(`/api/probabilistic/bayes-update`, payload).then(r => r.data),
  infer:          (payload)  => apiClient.post(`/api/probabilistic/infer`, payload).then(r => r.data),
  hmmTrack:       (payload)  => apiClient.post(`/api/probabilistic/hmm`, payload).then(r => r.data),
  getLiveWeather: ()         => apiClient.get(`/api/probabilistic/live-weather`).then(r => r.data),
  getLiveCrowds:  ()         => apiClient.get(`/api/probabilistic/live-crowds`).then(r => r.data),

  hybridPlan: (payload) => apiClient.post(`/api/hybrid/plan`, payload).then(r => r.data),
}
