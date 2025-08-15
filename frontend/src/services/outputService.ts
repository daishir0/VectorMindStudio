import { api } from './api';
import { PaginatedResponse, OutputDetailResponse } from '../types';

class OutputService {
  async getOutputs(page = 1, limit = 20): Promise<PaginatedResponse<OutputDetailResponse>> {
    return api.get('/api/v1/outputs', { params: { page, limit } });
  }

  async getOutput(id: string): Promise<OutputDetailResponse> {
    return api.get(`/api/v1/outputs/${id}`);
  }

  async getOutputDetails(outputId: string): Promise<OutputDetailResponse> {
    const response = await api.get<OutputDetailResponse>(`/api/v1/outputs/${outputId}`);
    return response;
  }

  async getOutputContent(outputId: string): Promise<{ content: string; output_id: string }> {
    const response = await api.get<{ content: string; output_id: string }>(`/api/v1/outputs/${outputId}/content`);
    return response;
  }

  async deleteOutput(outputId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/api/v1/outputs/${outputId}`);
    return response;
  }
}

export const outputService = new OutputService();
