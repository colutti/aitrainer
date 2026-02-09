/**
 * Date formatting utilities using Intl.DateTimeFormat
 * All formats use pt-BR locale
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

const formatters: Record<DateFormat, Intl.DateTimeFormat> = {
  short: new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }),
  medium: new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }),
  long: new Intl.DateTimeFormat('pt-BR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }),
  full: new Intl.DateTimeFormat('pt-BR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }),
  time: new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  }),
  timeWithSeconds: new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  }),
  monthYear: new Intl.DateTimeFormat('pt-BR', {
    month: 'long',
    year: 'numeric',
  }),
  dayMonth: new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
  }),
};

/**
 * Format a date using predefined formats
 *
 * @param date - Date to format (Date object, ISO string, or null/undefined)
 * @param format - Format preset to use
 * @returns Formatted date string, or empty string if date is invalid
 *
 * @example
 * ```ts
 * formatDate(new Date(), 'short') // "15/03/2024"
 * formatDate('2024-03-15T14:30:00', 'medium') // "15/03/2024 14:30"
 * formatDate(new Date(), 'long') // "15 de março de 2024"
 * ```
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

  return formatters[format].format(dateObj);
}
