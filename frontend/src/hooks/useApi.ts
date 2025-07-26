import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  userApi, 
  competitorApi, 
  promptApi, 
  llmResponseApi, 
  analyticsApi,
  User,
  Competitor,
  Prompt,
  LLMResponse,
  AnalyticsResult,
  DashboardSummary,
  CompetitorDiscoveryRequest,
  PromptGenerationRequest
} from '../lib/api'

// User hooks
export const useUser = (userId: string) => {
  return useQuery(['user', userId], () => userApi.get(userId), {
    enabled: !!userId,
  })
}

export const useCreateUser = () => {
  const queryClient = useQueryClient()
  return useMutation(userApi.create, {
    onSuccess: (data) => {
      queryClient.setQueryData(['user', data.data.id], data.data)
    },
  })
}

export const useUpdateUser = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, userData }: { userId: string; userData: Partial<User> }) =>
      userApi.update(userId, userData),
    {
      onSuccess: (data, { userId }) => {
        queryClient.setQueryData(['user', userId], data.data)
        queryClient.invalidateQueries(['user', userId])
      },
    }
  )
}

// Competitor hooks
export const useCompetitors = (userId: string) => {
  return useQuery(['competitors', userId], () => competitorApi.getAll(userId), {
    enabled: !!userId,
  })
}

export const useDiscoverCompetitors = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, request }: { userId: string; request: CompetitorDiscoveryRequest }) =>
      competitorApi.discover(userId, request),
    {
      onSuccess: (_, { userId }) => {
        queryClient.invalidateQueries(['competitors', userId])
      },
    }
  )
}

export const useCreateCompetitor = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, competitor }: { userId: string; competitor: Omit<Competitor, 'id' | 'user_id' | 'created_at' | 'updated_at'> }) =>
      competitorApi.create(userId, competitor),
    {
      onSuccess: (_, { userId }) => {
        queryClient.invalidateQueries(['competitors', userId])
      },
    }
  )
}

export const useUpdateCompetitor = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, competitorId, competitor }: { userId: string; competitorId: string; competitor: Partial<Competitor> }) =>
      competitorApi.update(userId, competitorId, competitor),
    {
      onSuccess: (_, { userId }) => {
        queryClient.invalidateQueries(['competitors', userId])
      },
    }
  )
}

export const useDeleteCompetitor = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, competitorId }: { userId: string; competitorId: string }) =>
      competitorApi.delete(userId, competitorId),
    {
      onSuccess: (_, { userId }) => {
        queryClient.invalidateQueries(['competitors', userId])
      },
    }
  )
}

// Prompt hooks
export const usePrompts = (userId: string, category?: string) => {
  return useQuery(['prompts', userId, category], () => promptApi.getAll(userId, category), {
    enabled: !!userId,
  })
}

export const useGeneratePrompts = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, request }: { userId: string; request: PromptGenerationRequest }) =>
      promptApi.generate(userId, request),
    {
      onSuccess: (_, { userId }) => {
        queryClient.invalidateQueries(['prompts', userId])
      },
    }
  )
}

export const useCreatePrompt = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, prompt }: { userId: string; prompt: Omit<Prompt, 'id' | 'user_id' | 'created_at' | 'updated_at'> }) =>
      promptApi.create(userId, prompt),
    {
      onSuccess: (_, { userId }) => {
        queryClient.invalidateQueries(['prompts', userId])
      },
    }
  )
}

export const useUpdatePrompt = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, promptId, prompt }: { userId: string; promptId: string; prompt: Partial<Prompt> }) =>
      promptApi.update(userId, promptId, prompt),
    {
      onSuccess: (_, { userId }) => {
        queryClient.invalidateQueries(['prompts', userId])
      },
    }
  )
}

export const useDeletePrompt = () => {
  const queryClient = useQueryClient()
  return useMutation(
    ({ userId, promptId }: { userId: string; promptId: string }) =>
      promptApi.delete(userId, promptId),
    {
      onSuccess: (_, { userId }) => {
        queryClient.invalidateQueries(['prompts', userId])
      },
    }
  )
}

export const usePromptCategories = (userId: string) => {
  return useQuery(['prompt-categories', userId], () => promptApi.getCategories(userId), {
    enabled: !!userId,
  })
}

// LLM Response hooks
export const useLLMResponses = (userId: string, params?: any) => {
  return useQuery(['llm-responses', userId, params], () => llmResponseApi.getAll(userId, params), {
    enabled: !!userId,
  })
}

export const useLLMResponse = (userId: string, responseId: string) => {
  return useQuery(['llm-response', userId, responseId], () => llmResponseApi.get(userId, responseId), {
    enabled: !!userId && !!responseId,
  })
}

export const useTestPrompt = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, promptId, data }: { userId: string; promptId: string; data: any }) => 
      llmResponseApi.testPrompt(userId, promptId, data),
    onSuccess: (_, { userId }) => {
      queryClient.invalidateQueries({ queryKey: ['llm-responses', userId] })
    },
  })
}

export const useStartBulkTest = () => {
  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: any }) => 
      llmResponseApi.startBulkTest(userId, data)
  })
}

export const useBulkTestStatus = (userId: string, testId: string, enabled: boolean = true) => {
  return useQuery(
    ['bulk-test-status', userId, testId], 
    () => llmResponseApi.getBulkTestStatus(userId, testId),
    {
      enabled: !!userId && !!testId && enabled,
      refetchInterval: (data) => {
        // Refetch every 5 seconds if the test is still running
        const status = data?.data?.status
        return status === 'pending' || status === 'running' ? 5000 : false
      }
    }
  )
}

// Analytics hooks
export const useDashboard = (userId: string) => {
  return useQuery(['dashboard', userId], () => analyticsApi.getDashboard(userId), {
    enabled: !!userId,
  })
}

export const useAnalyzeResponses = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, data }: { userId: string; data: any }) => 
      analyticsApi.analyzeResponses(userId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['analytics', variables.userId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', variables.userId] })
    },
  })
}

export const useCompetitorComparison = (userId: string) => {
  return useQuery(['competitor-comparison', userId], () => analyticsApi.getCompetitorComparison(userId), {
    enabled: !!userId,
  })
}

export const useModelPerformance = (userId: string) => {
  return useQuery(['model-performance', userId], () => analyticsApi.getModelPerformance(userId), {
    enabled: !!userId,
  })
}

export const useAnalyticsResult = (userId: string, analyticsId: string) => {
  return useQuery(['analytics-result', userId, analyticsId], () => analyticsApi.getResult(userId, analyticsId), {
    enabled: !!userId && !!analyticsId,
  })
}

export const useSearchResponses = (userId: string, query: string, enabled: boolean = true) => {
  return useQuery(['search-responses', userId, query], () => analyticsApi.search(userId, query), {
    enabled: !!userId && !!query && enabled,
  })
} 