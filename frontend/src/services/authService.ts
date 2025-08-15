import { api } from './api';
import { User, UserLogin, UserCreate, AuthToken, PasswordChange } from '../types';

export class AuthService {
  async login(credentials: UserLogin): Promise<AuthToken> {
    return await api.post<AuthToken>('/api/v1/auth/login', credentials);
  }

  async register(userData: UserCreate): Promise<User> {
    return await api.post<User>('/api/v1/auth/register', userData);
  }

  async logout(): Promise<void> {
    return await api.post('/api/v1/auth/logout');
  }

  async refreshToken(refreshToken: string): Promise<AuthToken> {
    return await api.post<AuthToken>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
  }

  async getCurrentUser(): Promise<User> {
    return await api.get<User>('/api/v1/auth/me');
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return await api.patch<User>('/api/v1/auth/me', data);
  }

  async changePassword(data: PasswordChange): Promise<void> {
    return await api.post('/api/v1/auth/change-password', data);
  }

  async requestPasswordReset(email: string): Promise<void> {
    return await api.post('/api/v1/auth/password-reset-request', { email });
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    return await api.post('/api/v1/auth/password-reset', {
      token,
      new_password: newPassword,
    });
  }

  async verifyEmail(token: string): Promise<void> {
    return await api.post('/api/v1/auth/verify-email', { token });
  }

  async resendVerificationEmail(): Promise<void> {
    return await api.post('/api/v1/auth/resend-verification');
  }

  // ユーティリティメソッド
  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    return !!token;
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  clearTokens(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  // トークンの有効期限チェック
  isTokenExpired(token?: string): boolean {
    const tokenToCheck = token || this.getToken();
    if (!tokenToCheck) return true;

    try {
      const payload = JSON.parse(atob(tokenToCheck.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch (error) {
      return true;
    }
  }

  // トークンからユーザーIDを取得
  getUserIdFromToken(token?: string): string | null {
    const tokenToCheck = token || this.getToken();
    if (!tokenToCheck) return null;

    try {
      const payload = JSON.parse(atob(tokenToCheck.split('.')[1]));
      return payload.sub || payload.user_id || null;
    } catch (error) {
      return null;
    }
  }

  // 権限チェック
  async hasPermission(permission: string): Promise<boolean> {
    try {
      return await api.get<boolean>(`/api/v1/auth/permissions/${permission}`);
    } catch (error) {
      return false;
    }
  }

  // ロールチェック
  async hasRole(role: string): Promise<boolean> {
    try {
      const user = await this.getCurrentUser();
      return user.roles.some(userRole => userRole === role);
    } catch (error) {
      return false;
    }
  }
}

export const authService = new AuthService();