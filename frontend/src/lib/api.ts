import axios, { AxiosResponse } from 'axios'

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface User {
  id: string
  email: string
  business_name: string
  website: string
  sector: string
  business_size: 'startup' | 'small' | 'medium' | 'large' | 'enterprise'
  location: string
  description?: string
  created_at: string
  updated_at: string
}

export interface Competitor {
  id: string
  user_id: string
  name: string
  website?: string
  description?: string
  is_auto_discovered: boolean
  created_at: string
  updated_at: string
}

export interface Prompt {
  id: string
  user_id: string
  content: string
  is_auto_generated: boolean
  category?: string
  created_at: string
  updated_at: string
}

export interface LLMResponse {
  id: string
  user_id: string
  prompt_id: string
  provider: 'openai' | 'anthropic' | 'gemini'
  model: string
  response_content: string
  response_metadata: Record<string, any>
  created_at: string
}

export interface AnalyticsResult {
  id: string
  user_id: string
  prompt_id: string
  llm_response_id: string
  user_brand_mentions: number
  competitor_mentions: Record<string, number>
  total_mentions: number
  mention_details: BrandMention[]
  analysis_metadata: Record<string, any>
  created_at: string
}

export interface BrandMention {
  brand_name: string
  mention_count: number
  mention_positions: number[]
  context_snippets: string[]
}

export interface DashboardSummary {
  total_prompts: number
  total_competitors: number
  total_responses: number
  user_brand_mention_rate: number
  top_competitor_mention_rate: number
  last_analysis_date?: string
}

export interface LLMConfiguration {
  provider: 'openai' | 'anthropic' | 'gemini'
  model: string
  is_active: boolean
}

export interface CompetitorDiscoveryRequest {
  api_key: string
  provider: 'openai' | 'anthropic' | 'gemini'
  model?: string
}

export interface PromptGenerationRequest {
  api_key: string
  provider: 'openai' | 'anthropic' | 'gemini'
  model?: string
  max_prompts?: number
}

// API functions
export const userApi = {
  create: (userData: Omit<User, 'id' | 'created_at' | 'updated_at'>) =>
    api.post<User>('/api/v1/users/', userData),
  
  get: (userId: string) =>
    api.get<User>(`/api/v1/users/${userId}`),
  
  update: (userId: string, userData: Partial<User>) =>
    api.put<User>(`/api/v1/users/${userId}`, userData),
  
  getByEmail: (email: string) =>
    api.get<User>(`/api/v1/users/email/${email}`),
}

export const competitorApi = {
  discover: (userId: string, request: CompetitorDiscoveryRequest) =>
    api.post(`/api/v1/competitors/${userId}/discover`, request),
  
  getAll: (userId: string) =>
    api.get<Competitor[]>(`/api/v1/competitors/${userId}`),
  
  create: (userId: string, competitor: Omit<Competitor, 'id' | 'user_id' | 'created_at' | 'updated_at'>) =>
    api.post<Competitor>(`/api/v1/competitors/${userId}`, competitor),
  
  update: (userId: string, competitorId: string, competitor: Partial<Competitor>) =>
    api.put<Competitor>(`/api/v1/competitors/${userId}/${competitorId}`, competitor),
  
  delete: (userId: string, competitorId: string) =>
    api.delete(`/api/v1/competitors/${userId}/${competitorId}`),
  
  refine: (userId: string, request: CompetitorDiscoveryRequest) =>
    api.post(`/api/v1/competitors/${userId}/refine`, request),
}

export const promptApi = {
  generate: (userId: string, request: PromptGenerationRequest) =>
    api.post(`/api/v1/prompts/${userId}/generate`, request),
  
  getAll: (userId: string, category?: string) =>
    api.get<Prompt[]>(`/api/v1/prompts/${userId}`, { params: { category } }),
  
  create: (userId: string, prompt: Omit<Prompt, 'id' | 'user_id' | 'created_at' | 'updated_at'>) =>
    api.post<Prompt>(`/api/v1/prompts/${userId}`, prompt),
  
  update: (userId: string, promptId: string, prompt: Partial<Prompt>) =>
    api.put<Prompt>(`/api/v1/prompts/${userId}/${promptId}`, prompt),
  
  delete: (userId: string, promptId: string) =>
    api.delete(`/api/v1/prompts/${userId}/${promptId}`),
  
  getCategories: (userId: string) =>
    api.get<{ categories: string[] }>(`/api/v1/prompts/${userId}/categories`),
}

export const llmResponseApi = {
  testPrompt: (userId: string, promptId: string, data: {
    configurations: LLMConfiguration[]
    api_keys: Record<string, string>
    iterations?: number
  }) =>
    api.post(`/api/v1/llm-responses/${userId}/test-prompt?prompt_id=${promptId}`, data),
  
  startBulkTest: (userId: string, data: {
    prompt_ids: string[]
    configurations: LLMConfiguration[]
    api_keys: Record<string, string>
    iterations_per_prompt?: number
  }) =>
    api.post(`/api/v1/llm-responses/${userId}/bulk-test`, data),
  
  getBulkTestStatus: (userId: string, testId: string) =>
    api.get(`/api/v1/llm-responses/${userId}/bulk-test/${testId}`),
  
  getAll: (userId: string, params?: {
    prompt_id?: string
    provider?: string
    model?: string
    limit?: number
  }) =>
    api.get<LLMResponse[]>(`/api/v1/llm-responses/${userId}/responses`, { params }),
  
  get: (userId: string, responseId: string) =>
    api.get<LLMResponse>(`/api/v1/llm-responses/${userId}/responses/${responseId}`),
  
  delete: (userId: string, responseId: string) =>
    api.delete(`/api/v1/llm-responses/${userId}/responses/${responseId}`),
}

export const analyticsApi = {
  analyzeResponses: (userId: string, data: {
    response_ids?: string[]
    api_key?: string
  }) =>
    api.post(`/api/v1/analytics/${userId}/analyze-responses`, data),
  
  getDashboard: (userId: string) =>
    api.get<DashboardSummary>(`/api/v1/analytics/${userId}/dashboard`),
  
  getCompetitorComparison: (userId: string) =>
    api.get(`/api/v1/analytics/${userId}/competitor-comparison`),
  
  getModelPerformance: (userId: string) =>
    api.get(`/api/v1/analytics/${userId}/model-performance`),
  
  getResult: (userId: string, analyticsId: string) =>
    api.get<AnalyticsResult>(`/api/v1/analytics/${userId}/analytics/${analyticsId}`),
  
  search: (userId: string, query: string) =>
    api.get(`/api/v1/analytics/${userId}/search`, { params: { query } }),
}

export default api 