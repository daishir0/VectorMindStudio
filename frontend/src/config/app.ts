// アプリケーション設定
export const APP_CONFIG = {
  // タイムゾーン設定
  timezone: 'Asia/Tokyo',
  
  // 日付・時間フォーマット設定
  dateFormat: {
    locale: 'ja-JP',
    options: {
      timeZone: 'Asia/Tokyo'
    }
  },
  
  // チャット設定
  chat: {
    maxMessageLength: 2000,
    scrollBehavior: 'smooth' as ScrollBehavior
  },
  
  // API設定
  api: {
    maxRetries: 3,
    timeout: 30000
  }
} as const;

// タイムゾーンを取得するヘルパー関数
export const getTimezone = () => APP_CONFIG.timezone;

// 日付フォーマット設定を取得するヘルパー関数  
export const getDateFormatConfig = () => APP_CONFIG.dateFormat;