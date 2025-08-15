import { api } from './api';
import { FileUploadResponse, PaginatedResponse, FileListResponse } from '../types';

export class FileService {
  async uploadFile(file: File, onUploadProgress: (progressEvent: any) => void): Promise<FileUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<FileUploadResponse>('/api/v1/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response;
  }

  async getFiles(
    page = 1, 
    limit = 20, 
    search?: string, 
    tags?: string[],
    sortField?: string,
    sortOrder?: string
  ): Promise<PaginatedResponse<FileListResponse>> {
    const params: any = { page, limit };
    
    if (search) {
      params.search = search;
    }
    
    if (tags && tags.length > 0) {
      params.tags = tags.join(',');
    }
    
    if (sortField) {
      params.sort_field = sortField;
    }
    
    if (sortOrder) {
      params.sort_order = sortOrder;
    }
    
    const response = await api.get<PaginatedResponse<FileListResponse>>('/api/v1/files', {
      params,
    });
    return response;
  }

  async getFileDetails(fileId: string): Promise<FileListResponse> {
    const response = await api.get<FileListResponse>(`/api/v1/files/${fileId}`);
    return response;
  }

  async getFileContent(fileId: string): Promise<{ content: string; filename: string }> {
    const response = await api.get<{ content: string; filename: string }>(`/api/v1/files/${fileId}/content`);
    return response;
  }

  async deleteFile(fileId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/api/v1/files/${fileId}`);
    return response;
  }

  async updateFileTags(fileId: string, tags: string[]): Promise<FileListResponse> {
    const response = await api.patch<FileListResponse>(`/api/v1/files/${fileId}/tags`, {
      tags,
    });
    return response;
  }

  async bulkUpdateTags(fileIds: string[], tags: string[]): Promise<{ updated_count: number }> {
    const response = await api.patch<{ updated_count: number }>('/api/v1/files/bulk/tags', {
      file_ids: fileIds,
      tags,
    });
    return response;
  }

  async bulkDeleteFiles(fileIds: string[]): Promise<{ deleted_count: number; failed_count: number; errors?: string[] }> {
    const response = await api.post<{ deleted_count: number; failed_count: number; errors?: string[] }>('/api/v1/files/bulk-delete', {
      file_ids: fileIds,
    });
    return response;
  }

  async getAllUserTags(): Promise<string[]> {
    const response = await api.get<string[]>('/api/v1/files/tags/all');
    return response;
  }
}

export const fileService = new FileService();
