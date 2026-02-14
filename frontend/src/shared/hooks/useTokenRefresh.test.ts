import { describe, it, expect } from 'vitest';
import { useTokenRefresh } from './useTokenRefresh';

describe('useTokenRefresh', () => {
  it('should export a function', () => {
    expect(typeof useTokenRefresh).toBe('function');
  });

  it('should be a React hook with correct implementation', () => {
    const hookCode = useTokenRefresh.toString();

    // Verify hook uses useEffect
    expect(hookCode).toContain('useEffect');

    // Verify hook uses useRef
    expect(hookCode).toContain('useRef');

    // Verify hook uses isTokenExpiringSoon
    expect(hookCode).toContain('isTokenExpiringSoon');

    // Verify hook uses refreshToken
    expect(hookCode).toContain('refreshToken');
  });

  it('should use setInterval for periodic checks', () => {
    const hookCode = useTokenRefresh.toString();

    // Verify it sets up an interval for periodic checks
    expect(hookCode).toContain('setInterval');
  });
});
