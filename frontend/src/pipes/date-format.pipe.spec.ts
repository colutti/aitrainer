import { AppDateFormatPipe } from './date-format.pipe';

describe('AppDateFormatPipe', () => {
  let pipe: AppDateFormatPipe;

  beforeEach(() => {
    pipe = new AppDateFormatPipe();
  });

  describe('Basic Functionality', () => {
    it('should create an instance', () => {
      expect(pipe).toBeTruthy();
    });

    it('should be standalone', () => {
      expect(pipe instanceof AppDateFormatPipe).toBe(true);
    });
  });

  describe('Format: short (dd/MM/yy)', () => {
    it('should format date as dd/MM/yy', () => {
      const date = new Date('2026-01-27');
      const result = pipe.transform(date, 'short');
      expect(result).toMatch(/^27\/01\/26$/);
    });

    it('should format with leading zeros', () => {
      const date = new Date('2026-03-05');
      const result = pipe.transform(date, 'short');
      expect(result).toMatch(/^05\/03\/26$/);
    });
  });

  describe('Format: medium (dd/MM/yyyy - default)', () => {
    it('should format date as dd/MM/yyyy', () => {
      const date = new Date('2026-01-27');
      const result = pipe.transform(date, 'medium');
      expect(result).toMatch(/^27\/01\/2026$/);
    });

    it('should use medium as default', () => {
      const date = new Date('2026-01-27');
      const resultDefault = pipe.transform(date);
      const resultMedium = pipe.transform(date, 'medium');
      expect(resultDefault).toBe(resultMedium);
    });

    it('should format various dates correctly', () => {
      const testCases = [
        { date: new Date('2026-01-05'), expected: /^05\/01\/2026$/ },
        { date: new Date('2026-12-31'), expected: /^31\/12\/2026$/ },
        { date: new Date('2026-07-15'), expected: /^15\/07\/2026$/ }
      ];

      testCases.forEach(test => {
        const result = pipe.transform(test.date, 'medium');
        expect(result).toMatch(test.expected);
      });
    });
  });

  describe('Format: long (dd MMM yyyy)', () => {
    it('should format date with month abbreviation', () => {
      const date = new Date('2026-01-27');
      const result = pipe.transform(date, 'long');
      expect(result).toMatch(/^27 de jan/i);
    });

    it('should use Portuguese abbreviations', () => {
      const months = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
        'jul', 'ago', 'set', 'out', 'nov', 'dez'];

      months.forEach((month, index) => {
        const date = new Date(2026, index, 15);
        const result = pipe.transform(date, 'long');
        expect(result?.toLowerCase()).toContain(month);
      });
    });
  });

  describe('Format: time (HH:mm)', () => {
    it('should format time only', () => {
      const date = new Date('2026-01-27T14:30:00');
      const result = pipe.transform(date, 'time');
      expect(result).toMatch(/^14:30$/);
    });

    it('should use 24-hour format', () => {
      const testCases = [
        { date: new Date('2026-01-27T00:00:00'), expected: /^00:00$/ },
        { date: new Date('2026-01-27T13:45:00'), expected: /^13:45$/ },
        { date: new Date('2026-01-27T23:59:00'), expected: /^23:59$/ }
      ];

      testCases.forEach(test => {
        const result = pipe.transform(test.date, 'time');
        expect(result).toMatch(test.expected);
      });
    });

    it('should handle minutes with leading zeros', () => {
      const date = new Date('2026-01-27T14:05:00');
      const result = pipe.transform(date, 'time');
      expect(result).toMatch(/^14:05$/);
    });
  });

  describe('Format: datetime (dd MMM yyyy • HH:mm)', () => {
    it('should format date and time together', () => {
      const date = new Date('2026-01-27T14:30:00');
      const result = pipe.transform(date, 'datetime');
      expect(result).toMatch(/^27 de jan.*2026.*14:30$/i);
    });

    it('should include separator', () => {
      const date = new Date('2026-01-27T10:00:00');
      const result = pipe.transform(date, 'datetime');
      expect(result).toContain('•');
    });
  });

  describe('Format: shortMonth (dd MMM)', () => {
    it('should format day and month only', () => {
      const date = new Date('2026-01-27');
      const result = pipe.transform(date, 'shortMonth');
      expect(result).toMatch(/^27 de jan/i);
    });

    it('should work for all months', () => {
      const months = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
        'jul', 'ago', 'set', 'out', 'nov', 'dez'];

      months.forEach((month, index) => {
        const date = new Date(2026, index, 15);
        const result = pipe.transform(date, 'shortMonth');
        expect(result?.toLowerCase()).toContain(month);
        expect(result).toContain('15');
      });
    });
  });

  describe('Format: dayMonth (dd/MM)', () => {
    it('should format day and month numerically', () => {
      const date = new Date('2026-01-27');
      const result = pipe.transform(date, 'dayMonth');
      expect(result).toMatch(/^27\/01$/);
    });

    it('should include leading zeros', () => {
      const testCases = [
        { date: new Date('2026-01-05'), expected: /^05\/01$/ },
        { date: new Date('2026-12-03'), expected: /^03\/12$/ }
      ];

      testCases.forEach(test => {
        const result = pipe.transform(test.date, 'dayMonth');
        expect(result).toMatch(test.expected);
      });
    });
  });

  describe('Format: full (dd/MM/yyyy HH:mm)', () => {
    it('should format complete date and time', () => {
      const date = new Date('2026-01-27T14:30:00');
      const result = pipe.transform(date, 'full');
      expect(result).toMatch(/^27\/01\/2026 14:30$/);
    });

    it('should include all components', () => {
      const date = new Date('2026-12-25T23:59:00');
      const result = pipe.transform(date, 'full');
      expect(result).toMatch(/^25\/12\/2026 23:59$/);
    });
  });

  describe('Edge Cases', () => {
    it('should handle null value', () => {
      expect(pipe.transform(null)).toBeNull();
    });

    it('should handle undefined value', () => {
      expect(pipe.transform(undefined)).toBeNull();
    });

    it('should handle invalid date string', () => {
      const result = pipe.transform('invalid-date', 'medium');
      expect(result).toBeNull();
    });

    it('should handle NaN date', () => {
      const result = pipe.transform(new Date('invalid'), 'medium');
      expect(result).toBeNull();
    });
  });

  describe('Custom Formats', () => {
    it('should support custom format strings', () => {
      const date = new Date('2026-01-27T14:30:00');
      const result = pipe.transform(date, 'dd/MM/yy - HH:mm');
      expect(result).toBeTruthy();
    });

    it('should fall back to custom format if preset not found', () => {
      const date = new Date('2026-01-27T14:30:00');
      const result = pipe.transform(date, 'dd MMMM yyyy');
      expect(result).toBeTruthy();
    });
  });

  describe('Locale: pt-BR', () => {
    it('should use Portuguese Brazil locale', () => {
      const date = new Date('2026-01-27');
      const result = pipe.transform(date, 'long');
      expect(result?.toLowerCase()).toContain('jan');
    });

    it('should format all 12 months', () => {
      const monthNames = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun',
        'jul', 'ago', 'set', 'out', 'nov', 'dez'];

      monthNames.forEach((month, index) => {
        const date = new Date(2026, index, 15);
        const result = pipe.transform(date, 'long');
        expect(result?.toLowerCase()).toContain(month);
      });
    });
  });
});
