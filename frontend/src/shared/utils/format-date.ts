import i18n from 'i18next';

/**
 * Date formatting utilities using Intl.DateTimeFormat
 * Locale is automatically detected from i18next
 */

export type DateFormat =
  | 'short' // dd/MM/yyyy
  | 'medium' // dd/MM/yyyy HH:mm
  | 'long' // dd de MMMM de yyyy
  | 'full' // dddd, dd de MMMM de yyyy
  | 'time' // HH:mm
  | 'timeWithSeconds' // HH:mm:ss
  | 'monthYear' // MMMM yyyy
  | 'dayMonth'; // dd/MM

// Simple cache for formatters per locale
const formatterCache = new Map<string, Record<DateFormat, Intl.DateTimeFormat>>();

/**
 * Get or create formatters for a specific locale
 */
function getFormatters(locale: string): Record<DateFormat, Intl.DateTimeFormat> {
  const cached = formatterCache.get(locale);
  if (cached) return cached;

  const newFormatters: Record<DateFormat, Intl.DateTimeFormat> = {
    short: new Intl.DateTimeFormat(locale, {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    }),
    medium: new Intl.DateTimeFormat(locale, {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    long: new Intl.DateTimeFormat(locale, {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }),
    full: new Intl.DateTimeFormat(locale, {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    }),
    time: new Intl.DateTimeFormat(locale, {
      hour: '2-digit',
      minute: '2-digit',
    }),
    timeWithSeconds: new Intl.DateTimeFormat(locale, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }),
    monthYear: new Intl.DateTimeFormat(locale, {
      month: 'long',
      year: 'numeric',
    }),
    dayMonth: new Intl.DateTimeFormat(locale, {
      day: '2-digit',
      month: '2-digit',
    }),
  };

  formatterCache.set(locale, newFormatters);
  return newFormatters;
}

/**
 * Format a date using predefined formats
 *
 * @param date - Date to format (Date object, ISO string, or null/undefined)
 * @param format - Format preset to use
 * @returns Formatted date string, or empty string if date is invalid
 */
export function formatDate(
  date: Date | string | null | undefined,
  format: DateFormat = 'short'
): string {
  if (!date) {
    return '';
  }

  const dateObj = typeof date === 'string' ? new Date(date) : date;

  // Check if date is valid
  if (Number.isNaN(dateObj.getTime())) {
    return '';
  }

  const locale = i18n.language || 'pt-BR';
  const formatters = getFormatters(locale);
  
  return formatters[format].format(dateObj);
}
