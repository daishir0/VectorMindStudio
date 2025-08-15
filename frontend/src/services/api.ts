import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8010';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // リクエストインターセプター（認証トークンを自動追加）
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // レスポンスインターセプター（エラーハンドリング）
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await this.client.post('/api/v1/auth/refresh', {
                refresh_token: refreshToken,
              });

              const { access_token } = response.data;
              localStorage.setItem('access_token', access_token);

              // 元のリクエストを再実行
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            // リフレッシュトークンも無効な場合はログアウト
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<ApiResponse<T>> = await this.client.get(url, config);
    return this.handleResponse(response);
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<ApiResponse<T>> = await this.client.post(url, data, config);
    return this.handleResponse(response);
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<ApiResponse<T>> = await this.client.put(url, data, config);
    return this.handleResponse(response);
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<ApiResponse<T>> = await this.client.patch(url, data, config);
    return this.handleResponse(response);
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<ApiResponse<T>> = await this.client.delete(url, config);
    return this.handleResponse(response);
  }

  // ファイルアップロード用のメソッド
  async uploadFile<T = any>(url: string, file: File, onUploadProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onUploadProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress(progress);
        }
      },
    };

    const response: AxiosResponse<ApiResponse<T>> = await this.client.post(url, formData, config);
    return this.handleResponse(response);
  }

  // ストリーミングレスポンス用のメソッド
  async getStream(url: string, config?: AxiosRequestConfig): Promise<ReadableStream> {
    const response = await this.client.get(url, {
      ...config,
      responseType: 'stream',
    });
    return response.data;
  }

  private handleResponse<T>(response: AxiosResponse<ApiResponse<T>>): T {
    const { data } = response;

    if (data.success) {
      return data.data as T;
    } else {
      const error = new Error(data.message || 'API request failed');
      (error as any).details = data.error;
      throw error;
    }
  }

  // 生のAxiosインスタンスを取得（特殊なケース用）
  getRawClient(): AxiosInstance {
    return this.client;
  }
}

// APIクライアントのシングルトンインスタンス
export const apiClient = new ApiClient();

// 便利な関数をエクスポート
export const api = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) => apiClient.get<T>(url, config),
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => apiClient.post<T>(url, data, config),
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => apiClient.put<T>(url, data, config),
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) => apiClient.patch<T>(url, data, config),
  delete: <T = any>(url: string, config?: AxiosRequestConfig) => apiClient.delete<T>(url, config),
  uploadFile: <T = any>(url: string, file: File, onUploadProgress?: (progress: number) => void) => 
    apiClient.uploadFile<T>(url, file, onUploadProgress),
  getStream: (url: string, config?: AxiosRequestConfig) => apiClient.getStream(url, config),
};

export default api;