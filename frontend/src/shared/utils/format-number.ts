import i18n from 'i18next';

/**
 * Number formatting utilities using Intl.NumberFormat
 * Locale is automatically detected from i18next
 */

export type NumberFormat =
  | 'decimal' // 1.234,56
  | 'integer' // 1.235
  | 'percent' // 50%
  | 'currency' // R$ 1.234,56
  | 'compact' // 1,5 mil
  | 'weight'; // 75,50 kg

/**
 * Format a number using predefined formats
 *
 * @param value - Number to format (or null/undefined)
 * @param format - Format preset to use
 * @param decimals - Number of decimal places (only for 'decimal' format, default: 2)
 * @returns Formatted number string, or empty string if value is invalid
 */
export function formatNumber(
  value: number | null | undefined,
  format: NumberFormat,
  decimals = 2
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '';
  }

  const locale = i18n.language || 'pt-BR';
  const currency = locale === 'pt-BR' ? 'BRL' : locale === 'es-ES' ? 'EUR' : 'USD';

  switch (format) {
    case 'decimal':
      return new Intl.NumberFormat(locale, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);

    case 'integer':
      return new Intl.NumberFormat(locale, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);

    case 'percent':
      return new Intl.NumberFormat(locale, {
        style: 'percent',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);

    case 'currency':
      return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency,
      }).format(value);

    case 'compact':
      return new Intl.NumberFormat(locale, {
        notation: 'compact',
        compactDisplay: 'short',
      }).format(value);

    case 'weight':
      return `${new Intl.NumberFormat(locale, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(value)} kg`;

    default:
      return value.toString();
  }
}
