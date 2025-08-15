import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { User, AuthState, UserLogin, UserCreate } from '../types';
import { authService } from '../services/authService';
import { toast } from 'react-hot-toast';

interface AuthContextType extends AuthState {
  login: (credentials: UserLogin) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'SET_TOKEN'; payload: string | null }
  | { type: 'LOGOUT' };

const initialState: AuthState = {
  user: null,
  token: localStorage.getItem('access_token'),
  isAuthenticated: false,
  isLoading: false,
};

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
      };
    case 'SET_TOKEN':
      return { ...state, token: action.payload };
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      };
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // 初期化時にトークンがある場合はユーザー情報を取得
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      // トークンの有効性をチェック
      if (authService.isTokenExpired(token)) {
        // 無効なトークンの場合はクリア
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        dispatch({ type: 'LOGOUT' });
      } else {
        loadUser();
      }
    } else {
      // トークンがない場合は確実にisLoadingをfalseに
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const loadUser = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const user = await authService.getCurrentUser();
      dispatch({ type: 'SET_USER', payload: user });
    } catch (error) {
      console.error('Failed to load user:', error);
      dispatch({ type: 'SET_LOADING', payload: false });
      logout();
    }
  };

  const login = async (credentials: UserLogin) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await authService.login(credentials);
      
      // トークンをローカルストレージに保存
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      
      dispatch({ type: 'SET_TOKEN', payload: response.access_token });
      
      // ユーザー情報を取得
      const user = await authService.getCurrentUser();
      dispatch({ type: 'SET_USER', payload: user });
      
      toast.success('ログインしました');
    } catch (error) {
      dispatch({ type: 'SET_LOADING', payload: false });
      const message = error instanceof Error ? error.message : 'ログインに失敗しました';
      toast.error(message);
      throw error;
    }
  };

  const register = async (userData: UserCreate) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      await authService.register(userData);
      
      dispatch({ type: 'SET_LOADING', payload: false });
      toast.success('アカウントが作成されました。ログインしてください。');
    } catch (error) {
      dispatch({ type: 'SET_LOADING', payload: false });
      const message = error instanceof Error ? error.message : '登録に失敗しました';
      toast.error(message);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    dispatch({ type: 'LOGOUT' });
    toast.success('ログアウトしました');
  };

  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await authService.refreshToken(refreshToken);
      localStorage.setItem('access_token', response.access_token);
      dispatch({ type: 'SET_TOKEN', payload: response.access_token });
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      throw error;
    }
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}