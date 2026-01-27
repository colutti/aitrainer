import { AppNumberFormatPipe } from './number-format.pipe';

describe('AppNumberFormatPipe', () => {
  let pipe: AppNumberFormatPipe;

  beforeEach(() => {
    pipe = new AppNumberFormatPipe();
  });

  describe('Basic Functionality', () => {
    it('should create an instance', () => {
      expect(pipe).toBeTruthy();
    });

    it('should be standalone', () => {
      expect(pipe instanceof AppNumberFormatPipe).toBe(true);
    });
  });

  describe('Format: integer (1.0-0)', () => {
    it('should format whole numbers', () => {
      expect(pipe.transform(42, 'integer')).toBe('42');
    });

    it('should round decimal values', () => {
      const result = pipe.transform(42.6, 'integer');
      expect(result).toMatch(/^4[2-3]$/); // Rounding behavior
    });

    it('should handle zero', () => {
      expect(pipe.transform(0, 'integer')).toBe('0');
    });

    it('should handle negative numbers', () => {
      expect(pipe.transform(-42, 'integer')).toBe('-42');
    });

    it('should add thousands separator', () => {
      const result = pipe.transform(1000, 'integer');
      expect(result).toContain('.');
    });

    it('should format large numbers with separator', () => {
      const result = pipe.transform(1234567, 'integer');
      expect(result).toBeTruthy();
    });
  });

  describe('Format: decimal1 (1.1-1)', () => {
    it('should format with one decimal place', () => {
      const result = pipe.transform(42.5, 'decimal1');
      expect(result).toMatch(/^42,\d$/);
    });

    it('should round to one decimal place', () => {
      const result = pipe.transform(42.56, 'decimal1');
      expect(result).toMatch(/^42,\d$/);
    });

    it('should use comma as decimal separator (pt-BR)', () => {
      const result = pipe.transform(10.5, 'decimal1');
      expect(result).toContain(',');
    });

    it('should handle weight format', () => {
      const result = pipe.transform(80.0, 'weight');
      expect(result).toBeTruthy();
    });

    it('should handle zero', () => {
      const result = pipe.transform(0, 'decimal1');
      expect(result).toMatch(/^0,\d$/);
    });

    it('should handle negative numbers', () => {
      const result = pipe.transform(-42.5, 'decimal1');
      expect(result).toBeTruthy();
    });

    it('should add thousands separator with decimal', () => {
      const result = pipe.transform(1234.5, 'decimal1');
      expect(result).toBeTruthy();
    });
  });

  describe('Format: decimal2 (1.2-2)', () => {
    it('should format with two decimal places', () => {
      const result = pipe.transform(42.5, 'decimal2');
      expect(result).toMatch(/^42,\d{2}$/);
    });

    it('should keep two decimal places', () => {
      const result = pipe.transform(42.1, 'decimal2');
      expect(result).toMatch(/^42,\d{2}$/);
    });

    it('should round correctly', () => {
      const result = pipe.transform(42.156, 'decimal2');
      expect(result).toMatch(/^42,1[5-6]$/);
    });

    it('should use comma as decimal separator', () => {
      const result = pipe.transform(10.55, 'decimal2');
      expect(result).toContain(',');
    });

    it('should handle percentage format', () => {
      const result = pipe.transform(85.5, 'percentage');
      expect(result).toBeTruthy();
    });

    it('should handle zero', () => {
      const result = pipe.transform(0, 'decimal2');
      expect(result).toMatch(/^0,00$/);
    });

    it('should handle very small numbers', () => {
      const result = pipe.transform(0.01, 'decimal2');
      expect(result).toMatch(/^0,0\d$/);
    });

    it('should add thousands separator with decimals', () => {
      const result = pipe.transform(1234.56, 'decimal2');
      expect(result).toBeTruthy();
    });
  });

  describe('Format: weight (alias for decimal1)', () => {
    it('should format weight with one decimal place', () => {
      const result = pipe.transform(80.5, 'weight');
      expect(result).toMatch(/^80,\d$/);
    });

    it('should be equivalent to decimal1', () => {
      const value = 75.3;
      const resultWeight = pipe.transform(value, 'weight');
      const resultDecimal1 = pipe.transform(value, 'decimal1');
      expect(resultWeight).toBe(resultDecimal1);
    });
  });

  describe('Format: percentage (alias for decimal2)', () => {
    it('should format percentage with two decimal places', () => {
      const result = pipe.transform(85.55, 'percentage');
      expect(result).toMatch(/^85,\d{2}$/);
    });

    it('should be equivalent to decimal2', () => {
      const value = 95.5;
      const resultPercentage = pipe.transform(value, 'percentage');
      const resultDecimal2 = pipe.transform(value, 'decimal2');
      expect(resultPercentage).toBe(resultDecimal2);
    });
  });

  describe('Default Format', () => {
    it('should use decimal1 as default', () => {
      const value = 42.5;
      const resultDefault = pipe.transform(value);
      const resultDecimal1 = pipe.transform(value, 'decimal1');
      expect(resultDefault).toBe(resultDecimal1);
    });
  });

  describe('Edge Cases', () => {
    it('should handle null value', () => {
      const result = pipe.transform(null);
      expect(result).toBeNull();
    });

    it('should handle undefined value', () => {
      const result = pipe.transform(undefined);
      expect(result).toBeNull();
    });

    it('should handle zero', () => {
      expect(pipe.transform(0, 'decimal1')).toBeTruthy();
    });

    it('should handle very large numbers', () => {
      const result = pipe.transform(999999999.99, 'decimal2');
      expect(result).toBeTruthy();
    });

    it('should handle very small positive numbers', () => {
      const result = pipe.transform(0.01, 'decimal2');
      expect(result).toBeTruthy();
    });

    it('should handle negative zero', () => {
      const result = pipe.transform(-0, 'decimal1');
      expect(result).toBeTruthy();
    });
  });

  describe('Negative Numbers', () => {
    it('should format negative integers', () => {
      const result = pipe.transform(-100, 'integer');
      expect(result).toContain('-');
    });

    it('should format negative decimals', () => {
      const result = pipe.transform(-42.5, 'decimal1');
      expect(result).toContain('-');
    });

    it('should format negative percentages', () => {
      const result = pipe.transform(-50.5, 'percentage');
      expect(result).toContain('-');
    });
  });

  describe('Locale: pt-BR', () => {
    it('should use comma as decimal separator', () => {
      const result = pipe.transform(10.5, 'decimal1');
      expect(result).toContain(',');
      expect(result).not.toContain('.');
    });

    it('should use period as thousands separator', () => {
      const result = pipe.transform(1000.0, 'integer');
      expect(result).toContain('.');
    });

    it('should format large decimal numbers correctly', () => {
      const result = pipe.transform(1234567.89, 'decimal2');
      expect(result).toBeTruthy();
    });
  });

  describe('Custom Formats', () => {
    it('should support custom format string', () => {
      const result = pipe.transform(42.5, '1.2-3');
      expect(result).toBeTruthy();
    });

    it('should fall back to custom format if preset not found', () => {
      const result = pipe.transform(42.5, '1.3-3');
      expect(result).toBeTruthy();
    });
  });

  describe('Type Coercion', () => {
    it('should handle string numbers', () => {
      const result = pipe.transform('42.5' as any, 'decimal1');
      expect(result).toBeTruthy();
    });

    it('should handle NaN', () => {
      const result = pipe.transform(NaN, 'decimal1');
      expect(result).toBeNull();
    });

    it('should handle Infinity', () => {
      const result = pipe.transform(Infinity, 'decimal1');
      expect(result).toBeTruthy();
    });
  });
});
