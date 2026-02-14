/**
 * Number formatting utilities using Intl.NumberFormat
 * All formats use pt-BR locale
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
 *
 * @example
 * ```ts
 * formatNumber(1234.56, 'decimal') // "1.234,56"
 * formatNumber(1234.56, 'integer') // "1.235"
 * formatNumber(0.5, 'percent') // "50%"
 * formatNumber(1234.56, 'currency') // "R$ 1.234,56"
 * formatNumber(1500, 'compact') // "1,5 mil"
 * formatNumber(75.5, 'weight') // "75,50 kg"
 * ```
 */
export function formatNumber(
  value: number | null | undefined,
  format: NumberFormat,
  decimals = 2
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '';
  }

  switch (format) {
    case 'decimal':
      return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);

    case 'integer':
      return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);

    case 'percent':
      return new Intl.NumberFormat('pt-BR', {
        style: 'percent',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);

    case 'currency':
      return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
      }).format(value);

    case 'compact':
      return new Intl.NumberFormat('pt-BR', {
        notation: 'compact',
        compactDisplay: 'short',
      }).format(value);

    case 'weight':
      return `${new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(value)} kg`;

    default:
      return value.toString();
  }
}
