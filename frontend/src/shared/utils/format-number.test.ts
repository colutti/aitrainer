import { describe, expect, it } from 'vitest';

import { formatNumber } from './format-number';

describe('formatNumber', () => {
  describe('decimal format', () => {
    it('should format number with 2 decimal places by default', () => {
      expect(formatNumber(1234.56, 'decimal')).toBe('1.234,56');
      expect(formatNumber(1000, 'decimal')).toBe('1.000,00');
      expect(formatNumber(0.5, 'decimal')).toBe('0,50');
    });

    it('should format number with custom decimal places', () => {
      expect(formatNumber(1234.567, 'decimal', 3)).toBe('1.234,567');
      expect(formatNumber(1234.5, 'decimal', 1)).toBe('1.234,5');
      expect(formatNumber(1234, 'decimal', 0)).toBe('1.234');
    });
  });

  describe('integer format', () => {
    it('should format number without decimal places', () => {
      expect(formatNumber(1234.56, 'integer')).toBe('1.235');
      expect(formatNumber(1000, 'integer')).toBe('1.000');
      expect(formatNumber(0.5, 'integer')).toBe('1');
    });
  });

  describe('percent format', () => {
    it('should format number as percentage', () => {
      expect(formatNumber(0.5, 'percent')).toBe('50%');
      expect(formatNumber(0.1234, 'percent')).toBe('12%');
      expect(formatNumber(1, 'percent')).toBe('100%');
      expect(formatNumber(0, 'percent')).toBe('0%');
    });
  });

  describe('currency format', () => {
    it('should format number as BRL currency', () => {
      // Intl uses non-breaking space (\u00A0) between currency symbol and number
      expect(formatNumber(1234.56, 'currency')).toBe('R$\u00A01.234,56');
      expect(formatNumber(0, 'currency')).toBe('R$\u00A00,00');
      expect(formatNumber(1000000, 'currency')).toBe('R$\u00A01.000.000,00');
    });
  });

  describe('compact format', () => {
    it('should format large numbers in compact notation', () => {
      // Intl uses non-breaking space (\u00A0) in compact notation
      expect(formatNumber(1000, 'compact')).toBe('1\u00A0mil');
      expect(formatNumber(1500, 'compact')).toBe('1,5\u00A0mil');
      expect(formatNumber(1000000, 'compact')).toBe('1\u00A0mi');
      expect(formatNumber(1500000, 'compact')).toBe('1,5\u00A0mi');
      expect(formatNumber(1000000000, 'compact')).toBe('1\u00A0bi');
    });

    it('should format small numbers without compacting', () => {
      expect(formatNumber(999, 'compact')).toBe('999');
      expect(formatNumber(100, 'compact')).toBe('100');
    });
  });

  describe('weight format', () => {
    it('should format weight in kg', () => {
      expect(formatNumber(75.5, 'weight')).toBe('75,5 kg');
      expect(formatNumber(100, 'weight')).toBe('100,0 kg');
      expect(formatNumber(0, 'weight')).toBe('0,0 kg');
    });
  });

  describe('Edge cases', () => {
    it('should handle null and return empty string', () => {
      expect(formatNumber(null, 'decimal')).toBe('');
    });

    it('should handle undefined and return empty string', () => {
      expect(formatNumber(undefined, 'decimal')).toBe('');
    });

    it('should handle NaN and return empty string', () => {
      expect(formatNumber(NaN, 'decimal')).toBe('');
    });

    it('should handle negative numbers', () => {
      expect(formatNumber(-1234.56, 'decimal')).toBe('-1.234,56');
      expect(formatNumber(-100, 'currency')).toBe('-R$\u00A0100,00');
      expect(formatNumber(-0.5, 'percent')).toBe('-50%');
    });

    it('should handle very large numbers', () => {
      expect(formatNumber(999999999999, 'decimal')).toBe('999.999.999.999,00');
      expect(formatNumber(1000000000000, 'compact')).toBe('1\u00A0tri');
    });

    it('should handle very small numbers', () => {
      expect(formatNumber(0.001, 'decimal')).toBe('0,00');
      expect(formatNumber(0.001, 'decimal', 3)).toBe('0,001');
    });
  });
});
