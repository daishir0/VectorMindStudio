import { api } from './api';
import {
  Template,
  TemplateCreate,
  TemplateUpdate,
  TemplateUse,
  TemplateSearch,
  PaginatedResponse,
  AIOutput,
  SearchFilters,
} from '../types';

export class TemplateService {
  // テンプレート一覧取得
  async getTemplates(params?: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
  }): Promise<PaginatedResponse<Template>> {
    const searchParams = new URLSearchParams();
    
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.search) searchParams.set('search', params.search);
    if (params?.status) searchParams.set('status', params.status);

    return await api.get<PaginatedResponse<Template>>(`/api/v1/templates?${searchParams}`);
  }

  // テンプレート詳細取得
  async getTemplate(id: string): Promise<Template> {
    return await api.get<Template>(`/api/v1/templates/${id}`);
  }

  // テンプレート作成
  async createTemplate(data: TemplateCreate): Promise<Template> {
    return await api.post<Template>('/api/v1/templates', data);
  }

  // テンプレート更新
  async updateTemplate(id: string, data: TemplateUpdate): Promise<Template> {
    return await api.patch<Template>(`/api/v1/templates/${id}`, data);
  }

  // テンプレート削除
  async deleteTemplate(id: string): Promise<void> {
    return await api.delete(`/api/v1/templates/${id}`);
  }

  // テンプレート複製
  async duplicateTemplate(id: string, name?: string): Promise<Template> {
    return await api.post<Template>(`/api/v1/templates/${id}/duplicate`, { name });
  }

  // テンプレート使用
  async useTemplate(id: string, data: TemplateUse): Promise<AIOutput> {
    return await api.post<AIOutput>(`/api/v1/templates/${id}/use`, data);
  }

  // テンプレート検索
  async searchTemplates(query: TemplateSearch): Promise<Template[]> {
    return await api.post<Template[]>('/api/v1/templates/search', query);
  }

  // 類似テンプレート取得
  async getSimilarTemplates(id: string, limit = 5): Promise<Template[]> {
    return await api.get<Template[]>(`/api/v1/templates/${id}/similar?limit=${limit}`);
  }

  // 人気テンプレート取得
  async getPopularTemplates(limit = 10): Promise<Template[]> {
    return await api.get<Template[]>(`/api/v1/templates/popular?limit=${limit}`);
  }

  // 最近のテンプレート取得
  async getRecentTemplates(limit = 10): Promise<Template[]> {
    return await api.get<Template[]>(`/api/v1/templates/recent?limit=${limit}`);
  }

  // ユーザーのテンプレート取得
  async getUserTemplates(userId?: string, params?: {
    page?: number;
    limit?: number;
    status?: string;
  }): Promise<PaginatedResponse<Template>> {
    const searchParams = new URLSearchParams();
    
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.status) searchParams.set('status', params.status);

    const url = userId 
      ? `/api/v1/users/${userId}/templates?${searchParams}`
      : `/api/v1/templates/mine?${searchParams}`;

    return await api.get<PaginatedResponse<Template>>(url);
  }


  // テンプレートの統計情報取得
  async getTemplateStats(id: string): Promise<{
    usage_count: number;
    success_rate: number;
    avg_processing_time: number;
    recent_uses: AIOutput[];
  }> {
    return await api.get(`/api/v1/templates/${id}/stats`);
  }

  // テンプレートのバージョン履歴取得
  async getTemplateVersions(id: string): Promise<Template[]> {
    return await api.get<Template[]>(`/api/v1/templates/${id}/versions`);
  }

  // テンプレートのエクスポート
  async exportTemplate(id: string, format = 'json'): Promise<Blob> {
    const response = await api.getRawClient().get(`/api/v1/templates/${id}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  // テンプレートのインポート
  async importTemplate(file: File): Promise<Template> {
    return await api.uploadFile<Template>('/api/v1/templates/import', file);
  }

  // テンプレートの共有設定
  async shareTemplate(id: string, isPublic: boolean): Promise<Template> {
    return await api.patch<Template>(`/api/v1/templates/${id}/share`, { is_public: isPublic });
  }

  // 共有テンプレート一覧取得
  async getSharedTemplates(params?: {
    page?: number;
    limit?: number;
    search?: string;
    category?: string;
  }): Promise<PaginatedResponse<Template>> {
    const searchParams = new URLSearchParams();
    
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.search) searchParams.set('search', params.search);
    if (params?.category) searchParams.set('category', params.category);

    return await api.get<PaginatedResponse<Template>>(`/api/v1/templates/shared?${searchParams}`);
  }

  // テンプレートの評価
  async rateTemplate(id: string, rating: number, comment?: string): Promise<void> {
    return await api.post(`/api/v1/templates/${id}/rate`, { rating, comment });
  }

  // テンプレートの評価一覧取得
  async getTemplateRatings(id: string): Promise<{
    average_rating: number;
    total_ratings: number;
    ratings: Array<{
      rating: number;
      comment?: string;
      user_name: string;
      created_at: string;
    }>;
  }> {
    return await api.get(`/api/v1/templates/${id}/ratings`);
  }
}

export const templateService = new TemplateService();