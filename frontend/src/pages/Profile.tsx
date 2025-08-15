import React, { useState } from 'react';
import { User, Mail, Calendar, Shield, Edit2, Save, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import { UserUpdate, PasswordChange } from '../types';

const Profile: React.FC = () => {
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [profileData, setProfileData] = useState<UserUpdate>({
    username: user?.username || '',
    email: user?.email || '',
    full_name: user?.full_name || ''
  });

  const [passwordData, setPasswordData] = useState<PasswordChange>({
    current_password: '',
    new_password: ''
  });

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setErrors({});

      const updatedUser = await api.patch('/api/v1/auth/me', profileData);
      // TODO: Update user in context if needed
      setIsEditing(false);
    } catch (error: any) {
      console.error('Profile update failed:', error);
      
      if (error.response?.data?.detail) {
        setErrors({ general: error.response.data.detail });
      } else {
        setErrors({ general: 'プロフィールの更新に失敗しました。' });
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (passwordData.new_password.length < 8) {
      setErrors({ password: 'パスワードは8文字以上で入力してください' });
      return;
    }

    try {
      setLoading(true);
      setErrors({});

      await api.post('/api/v1/auth/change-password', passwordData);
      setIsChangingPassword(false);
      setPasswordData({ current_password: '', new_password: '' });
      
      // 成功メッセージを表示（ここではアラートを使用）
      alert('パスワードが変更されました。');
    } catch (error: any) {
      console.error('Password change failed:', error);
      
      if (error.response?.data?.detail) {
        setErrors({ password: error.response.data.detail });
      } else {
        setErrors({ password: 'パスワードの変更に失敗しました。' });
      }
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900">ユーザー情報が見つかりません</h2>
        <p className="mt-2 text-gray-600">ログインしてください。</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">プロフィール</h1>
          <p className="mt-1 text-sm text-gray-600">
            アカウント情報の表示と編集
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* プロフィール情報 */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900">基本情報</h2>
                {!isEditing && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <Edit2 className="h-4 w-4 mr-2" />
                    編集
                  </button>
                )}
              </div>
            </div>

            <div className="px-6 py-6">
              {errors.general && (
                <div className="mb-4 rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-700">{errors.general}</div>
                </div>
              )}

              {isEditing ? (
                <form onSubmit={handleProfileUpdate} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      ユーザー名
                    </label>
                    <input
                      type="text"
                      className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      value={profileData.username}
                      onChange={(e) => setProfileData({ ...profileData, username: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      メールアドレス
                    </label>
                    <input
                      type="email"
                      className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      フルネーム
                    </label>
                    <input
                      type="text"
                      className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      value={profileData.full_name || ''}
                      onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                    />
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => {
                        setIsEditing(false);
                        setProfileData({
                          username: user.username,
                          email: user.email,
                          full_name: user.full_name
                        });
                        setErrors({});
                      }}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      <X className="h-4 w-4 mr-2" />
                      キャンセル
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                      {loading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          保存中...
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4 mr-2" />
                          保存
                        </>
                      )}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center">
                    <User className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">ユーザー名</div>
                      <div className="text-sm text-gray-600">{user.username}</div>
                    </div>
                  </div>

                  <div className="flex items-center">
                    <Mail className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">メールアドレス</div>
                      <div className="text-sm text-gray-600">{user.email}</div>
                    </div>
                  </div>

                  {user.full_name && (
                    <div className="flex items-center">
                      <User className="h-5 w-5 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-gray-900">フルネーム</div>
                        <div className="text-sm text-gray-600">{user.full_name}</div>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center">
                    <Calendar className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">アカウント作成日</div>
                      <div className="text-sm text-gray-600">
                        {new Date(user.created_at).toLocaleDateString('ja-JP')}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center">
                    <Shield className="h-5 w-5 text-gray-400 mr-3" />
                    <div>
                      <div className="text-sm font-medium text-gray-900">ロール</div>
                      <div className="text-sm text-gray-600">
                        {user.roles?.map(role => role.replace('_', ' ')).join(', ') || 'User'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* セキュリティ設定 */}
        <div>
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">セキュリティ</h2>
            </div>

            <div className="px-6 py-6">
              <div className="space-y-4">
                <div>
                  <div className="text-sm font-medium text-gray-900">パスワード</div>
                  <div className="text-sm text-gray-600">最終変更: 不明</div>
                </div>

                {!isChangingPassword ? (
                  <button
                    onClick={() => setIsChangingPassword(true)}
                    className="w-full inline-flex justify-center items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    パスワードを変更
                  </button>
                ) : (
                  <form onSubmit={handlePasswordChange} className="space-y-3">
                    {errors.password && (
                      <div className="rounded-md bg-red-50 p-3">
                        <div className="text-sm text-red-700">{errors.password}</div>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        現在のパスワード
                      </label>
                      <input
                        type="password"
                        required
                        className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        value={passwordData.current_password}
                        onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        新しいパスワード
                      </label>
                      <input
                        type="password"
                        required
                        className="mt-1 shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                        value={passwordData.new_password}
                        onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                      />
                    </div>

                    <div className="flex space-x-2">
                      <button
                        type="button"
                        onClick={() => {
                          setIsChangingPassword(false);
                          setPasswordData({ current_password: '', new_password: '' });
                          setErrors({});
                        }}
                        className="flex-1 inline-flex justify-center items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                      >
                        キャンセル
                      </button>
                      <button
                        type="submit"
                        disabled={loading}
                        className="flex-1 inline-flex justify-center items-center px-3 py-2 border border-transparent shadow-sm text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                      >
                        {loading ? '変更中...' : '変更'}
                      </button>
                    </div>
                  </form>
                )}

                <div className="pt-4 border-t border-gray-200">
                  <div className="text-sm font-medium text-gray-900">アカウントステータス</div>
                  <div className="mt-1 flex items-center">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'アクティブ' : '無効'}
                    </span>
                    {user.is_verified && (
                      <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        認証済み
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;