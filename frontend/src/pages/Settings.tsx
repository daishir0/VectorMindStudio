import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Bell,
  Globe,
  Moon,
  Sun,
  Monitor,
  Database,
  Download,
  Trash2,
  Save,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const Settings: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // 設定状態
  const [settings, setSettings] = useState({
    language: 'ja',
    theme: 'system',
    notifications: {
      email: true,
      browser: false,
      updates: true,
    },
    display: {
      compactMode: false,
      showLineNumbers: true,
      fontSize: 'medium',
    },
    api: {
      timeout: 30000,
      retryAttempts: 3,
    },
  });

  const handleSaveSettings = async () => {
    try {
      setLoading(true);
      // TODO: API call to save settings
      await new Promise((resolve) => setTimeout(resolve, 1000));
      alert('設定を保存しました');
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('設定の保存に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    try {
      setLoading(true);
      // TODO: API call to export data
      await new Promise((resolve) => setTimeout(resolve, 1000));
      alert('データをエクスポートしました');
    } catch (error) {
      console.error('Failed to export data:', error);
      alert('データのエクスポートに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      setLoading(true);
      // TODO: API call to delete account
      await new Promise((resolve) => setTimeout(resolve, 1000));
      alert('アカウントを削除しました');
    } catch (error) {
      console.error('Failed to delete account:', error);
      alert('アカウントの削除に失敗しました');
    } finally {
      setLoading(false);
      setShowDeleteConfirm(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">設定</h1>
          <p className="mt-1 text-sm text-gray-600">
            アプリケーションの設定とカスタマイズ
          </p>
        </div>
        <button
          onClick={handleSaveSettings}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              保存中...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              設定を保存
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 一般設定 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <SettingsIcon className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">一般設定</h2>
            </div>
          </div>
          <div className="px-6 py-6 space-y-6">
            {/* 言語設定 */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Globe className="h-4 w-4 mr-2" />
                言語
              </label>
              <select
                value={settings.language}
                onChange={(e) =>
                  setSettings({ ...settings, language: e.target.value })
                }
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="ja">日本語</option>
                <option value="en">English</option>
                <option value="zh">中文</option>
              </select>
            </div>

            {/* テーマ設定 */}
            <div>
              <label className="flex items-center text-sm font-medium text-gray-700 mb-2">
                <Sun className="h-4 w-4 mr-2" />
                テーマ
              </label>
              <div className="mt-2 space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="theme"
                    value="light"
                    checked={settings.theme === 'light'}
                    onChange={(e) =>
                      setSettings({ ...settings, theme: e.target.value })
                    }
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <Sun className="ml-3 mr-2 h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700">ライトモード</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="theme"
                    value="dark"
                    checked={settings.theme === 'dark'}
                    onChange={(e) =>
                      setSettings({ ...settings, theme: e.target.value })
                    }
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <Moon className="ml-3 mr-2 h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700">ダークモード</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    name="theme"
                    value="system"
                    checked={settings.theme === 'system'}
                    onChange={(e) =>
                      setSettings({ ...settings, theme: e.target.value })
                    }
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300"
                  />
                  <Monitor className="ml-3 mr-2 h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-700">システム設定に従う</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* 通知設定 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <Bell className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">通知設定</h2>
            </div>
          </div>
          <div className="px-6 py-6 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">メール通知</div>
                <div className="text-sm text-gray-600">重要な更新をメールで受信</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notifications.email}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      notifications: {
                        ...settings.notifications,
                        email: e.target.checked,
                      },
                    })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">ブラウザ通知</div>
                <div className="text-sm text-gray-600">デスクトップ通知を表示</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notifications.browser}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      notifications: {
                        ...settings.notifications,
                        browser: e.target.checked,
                      },
                    })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">アップデート通知</div>
                <div className="text-sm text-gray-600">新機能のお知らせを受信</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.notifications.updates}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      notifications: {
                        ...settings.notifications,
                        updates: e.target.checked,
                      },
                    })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* 表示設定 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <Monitor className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">表示設定</h2>
            </div>
          </div>
          <div className="px-6 py-6 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">コンパクトモード</div>
                <div className="text-sm text-gray-600">画面をコンパクトに表示</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.display.compactMode}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      display: {
                        ...settings.display,
                        compactMode: e.target.checked,
                      },
                    })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">行番号表示</div>
                <div className="text-sm text-gray-600">エディタで行番号を表示</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.display.showLineNumbers}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      display: {
                        ...settings.display,
                        showLineNumbers: e.target.checked,
                      },
                    })
                  }
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                フォントサイズ
              </label>
              <select
                value={settings.display.fontSize}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    display: { ...settings.display, fontSize: e.target.value },
                  })
                }
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="small">小</option>
                <option value="medium">中</option>
                <option value="large">大</option>
              </select>
            </div>
          </div>
        </div>

        {/* API設定 */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <Database className="h-5 w-5 text-gray-400 mr-2" />
              <h2 className="text-lg font-medium text-gray-900">API設定</h2>
            </div>
          </div>
          <div className="px-6 py-6 space-y-6">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                タイムアウト (ミリ秒)
              </label>
              <input
                type="number"
                value={settings.api.timeout}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    api: { ...settings.api, timeout: parseInt(e.target.value) },
                  })
                }
                className="mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
              />
              <p className="mt-1 text-sm text-gray-500">
                APIリクエストのタイムアウト時間（デフォルト: 30000ms）
              </p>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                リトライ回数
              </label>
              <input
                type="number"
                value={settings.api.retryAttempts}
                onChange={(e) =>
                  setSettings({
                    ...settings,
                    api: {
                      ...settings.api,
                      retryAttempts: parseInt(e.target.value),
                    },
                  })
                }
                className="mt-1 shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
              />
              <p className="mt-1 text-sm text-gray-500">
                失敗時のリトライ回数（デフォルト: 3回）
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* データ管理 */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">データ管理</h2>
        </div>
        <div className="px-6 py-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-gray-900">データのエクスポート</div>
                <div className="text-sm text-gray-600">
                  すべてのデータをJSON形式でエクスポート
                </div>
              </div>
              <button
                onClick={handleExportData}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <Download className="h-4 w-4 mr-2" />
                エクスポート
              </button>
            </div>

            <div className="pt-4 border-t border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center text-sm font-medium text-red-900">
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    アカウントの削除
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    アカウントとすべてのデータを完全に削除します。この操作は取り消せません。
                  </div>
                </div>
                {!showDeleteConfirm ? (
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="inline-flex items-center px-4 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    削除
                  </button>
                ) : (
                  <div className="flex space-x-2">
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                    >
                      キャンセル
                    </button>
                    <button
                      onClick={handleDeleteAccount}
                      disabled={loading}
                      className="inline-flex items-center px-3 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                    >
                      削除を確認
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
