import { describe, expect, it } from 'vitest';

import { cn } from './cn';

describe('cn utility', () => {
  it('should merge classes correctly', () => {
    expect(cn('class1', 'class2')).toBe('class1 class2');
  });

  it('should handle conditional classes', () => {
    const isTrue = true;
    const isFalse = false;
    expect(cn('class1', isTrue && 'class2', isFalse && 'class3')).toBe('class1 class2');
  });

  it('should merge tailwind classes correctly', () => {
    // tailwind-merge should resolve conflicts
    expect(cn('px-2 py-2', 'px-4')).toBe('py-2 px-4');
  });

  it('should handle undefined and null', () => {
    expect(cn('class1', undefined, null)).toBe('class1');
  });
});
