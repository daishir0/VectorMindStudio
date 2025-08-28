import { getTimezone } from '../config/app';

/**
 * UTC時間文字列を正しく解釈してDateオブジェクトに変換
 * バックエンドからのUTC時間文字列（"2023-12-01T12:00:00"）を
 * 明示的にUTCとして扱う
 */
export const parseUTCDateTime = (utcTimeString: string | Date): Date => {
  if (utcTimeString instanceof Date) {
    return utcTimeString;
  }
  
  // UTC文字列に"Z"を付加してUTCとして明示的に解釈
  const utcString = utcTimeString.includes('Z') ? utcTimeString : `${utcTimeString}Z`;
  return new Date(utcString);
};

/**
 * 時間を日本のタイムゾーンでフォーマット
 */
export const formatTimeWithTimezone = (dateTime: string | Date, options: Intl.DateTimeFormatOptions = {}): string => {
  const date = parseUTCDateTime(dateTime);
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    hour: '2-digit',
    minute: '2-digit',
    timeZone: getTimezone(),
    ...options
  };
  
  return date.toLocaleTimeString('ja-JP', defaultOptions);
};

/**
 * 日付を日本のタイムゾーンでフォーマット
 */
export const formatDateWithTimezone = (dateTime: string | Date, options: Intl.DateTimeFormatOptions = {}): string => {
  const date = parseUTCDateTime(dateTime);
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: getTimezone(),
    ...options
  };
  
  return date.toLocaleString('ja-JP', defaultOptions);
};