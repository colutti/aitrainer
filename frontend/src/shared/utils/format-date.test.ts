import { describe, expect, it } from 'vitest';

import { formatDate } from './format-date';

describe('formatDate', () => {
  // Fixed date for consistent testing: 2024-03-15 14:30:45
  const testDate = new Date('2024-03-15T14:30:45');
  const testDateString = '2024-03-15T14:30:45';

  describe('short format', () => {
    it('should format date as dd/MM/yyyy', () => {
      expect(formatDate(testDate, 'short')).toBe('15/03/2024');
      expect(formatDate(testDateString, 'short')).toBe('15/03/2024');
    });
  });

  describe('medium format', () => {
    it('should format date as dd/MM/yyyy HH:mm', () => {
      // Intl.DateTimeFormat adds a comma between date and time
      expect(formatDate(testDate, 'medium')).toBe('15/03/2024, 14:30');
      expect(formatDate(testDateString, 'medium')).toBe('15/03/2024, 14:30');
    });
  });

  describe('long format', () => {
    it('should format date as dd de MMMM de yyyy', () => {
      const result = formatDate(testDate, 'long');
      expect(result).toContain('15');
      expect(result).toContain('março');
      expect(result).toContain('2024');
    });
  });

  describe('full format', () => {
    it('should format date as dddd, dd de MMMM de yyyy', () => {
      const result = formatDate(testDate, 'full');
      expect(result).toContain('15');
      expect(result).toContain('março');
      expect(result).toContain('2024');
    });
  });

  describe('time format', () => {
    it('should format time as HH:mm', () => {
      expect(formatDate(testDate, 'time')).toBe('14:30');
    });
  });

  describe('timeWithSeconds format', () => {
    it('should format time as HH:mm:ss', () => {
      expect(formatDate(testDate, 'timeWithSeconds')).toBe('14:30:45');
    });
  });

  describe('monthYear format', () => {
    it('should format as MMMM yyyy', () => {
      const result = formatDate(testDate, 'monthYear');
      expect(result).toContain('março');
      expect(result).toContain('2024');
    });
  });

  describe('dayMonth format', () => {
    it('should format as dd/MM', () => {
      expect(formatDate(testDate, 'dayMonth')).toBe('15/03');
    });
  });

  describe('Edge cases', () => {
    it('should handle null and return empty string', () => {
      expect(formatDate(null, 'short')).toBe('');
    });

    it('should handle undefined and return empty string', () => {
      expect(formatDate(undefined, 'short')).toBe('');
    });

    it('should handle invalid date string and return empty string', () => {
      expect(formatDate('invalid-date', 'short')).toBe('');
    });

    it('should handle NaN date and return empty string', () => {
      expect(formatDate(new Date('invalid'), 'short')).toBe('');
    });
  });
});
