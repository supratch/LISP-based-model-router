import { useState, useCallback } from 'react';
import axios from 'axios';

interface QueryRequest {
  query: string;
  context?: any;
  priority?: string;
  source_eid?: string;
  preferred_model?: string;
}

interface RoutingResponse {
  selected_model: string;
  routing_method: string;
  endpoint: string;
  confidence_score: number;
  reasoning: string;
  estimated_cost: number;
  estimated_response_time: number;
  alternative_models: string[];
  routing_metadata: any;
  llm_response?: string;
  generation_time?: number;
}

interface HealthResponse {
  status: string;
  timestamp: string;
  services: { [key: string]: string };
  uptime_seconds: number;
}

interface StatsResponse {
  lisp_stats: any;
  dns_stats: any;
  llm_stats: any;
  system_stats: any;
}

class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export const useAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Create axios instance with default config
  const createAxiosInstance = useCallback(() => {
    const instance = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
      timeout: 30000, // 30 seconds timeout
      headers: {
        'Content-Type': 'application/json',
        // In production, add proper authentication token
        'Authorization': 'Bearer demo-token'
      }
    });
    
    // Add response interceptor for error handling
    instance.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred';
        const status = error.response?.status;
        throw new APIError(message, status, error.response?.data);
      }
    );
    
    return instance;
  }, []);
  
  const handleRequest = useCallback(async <T>(request: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await request();
      return result;
    } catch (err) {
      const errorMessage = err instanceof APIError ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);
  
  // API methods
  const routeQuery = useCallback(async (request: QueryRequest): Promise<RoutingResponse> => {
    return handleRequest(async () => {
      const api = createAxiosInstance();
      const response = await api.post<RoutingResponse>('/route', request);
      return response.data;
    });
  }, [createAxiosInstance, handleRequest]);
  
  const getHealth = useCallback(async (): Promise<HealthResponse> => {
    return handleRequest(async () => {
      const api = createAxiosInstance();
      const response = await api.get<HealthResponse>('/health');
      return response.data;
    });
  }, [createAxiosInstance, handleRequest]);
  
  const getStats = useCallback(async (): Promise<StatsResponse> => {
    return handleRequest(async () => {
      const api = createAxiosInstance();
      const response = await api.get<StatsResponse>('/stats');
      return response.data;
    });
  }, [createAxiosInstance, handleRequest]);
  
  const getModels = useCallback(async (): Promise<{ models: { [key: string]: any } }> => {
    return handleRequest<{ models: { [key: string]: any } }>(async () => {
      const api = createAxiosInstance();
      const response = await api.get<{ models: { [key: string]: any } }>('/models');
      return response.data;
    });
  }, [createAxiosInstance, handleRequest]);

  const updateConfiguration = useCallback(async (service: string, config: any): Promise<any> => {
    return handleRequest<any>(async () => {
      const api = createAxiosInstance();
      const response = await api.post<any>('/config', { service, config });
      return response.data;
    });
  }, [createAxiosInstance, handleRequest]);

  const updateServiceWeight = useCallback(async (
    serviceName: string,
    recordName: string,
    weight: number
  ): Promise<any> => {
    return handleRequest<any>(async () => {
      const api = createAxiosInstance();
      const response = await api.post<any>(`/services/${serviceName}/weight`, null, {
        params: { record_name: recordName, weight }
      });
      return response.data;
    });
  }, [createAxiosInstance, handleRequest]);

  const getMetrics = useCallback(async (): Promise<string> => {
    return handleRequest<string>(async () => {
      const api = createAxiosInstance();
      const response = await api.get<string>('/metrics', {
        headers: { 'Accept': 'text/plain' }
      });
      return response.data;
    });
  }, [createAxiosInstance, handleRequest]);
  
  // Utility method to clear error state
  const clearError = useCallback(() => {
    setError(null);
  }, []);
  
  return {
    // State
    loading,
    error,
    
    // API methods
    routeQuery,
    getHealth,
    getStats,
    getModels,
    updateConfiguration,
    updateServiceWeight,
    getMetrics,
    
    // Utilities
    clearError
  };
};

export default useAPI;