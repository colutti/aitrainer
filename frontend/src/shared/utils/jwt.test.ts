import { describe, expect, it } from 'vitest';

import { decodeJwtPayload, getTokenExpiryMs, isTokenExpiringSoon } from './jwt';

// A real JWT with known exp claim: { sub: "test@test.com", exp: 9999999999 }
const FUTURE_TOKEN =
  'eyJhbGciOiJIUzI1NiJ9.' +
  btoa(JSON.stringify({ sub: 'test@test.com', exp: 9999999999 }))
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_') +
  '.signature';

const PAST_TOKEN =
  'eyJhbGciOiJIUzI1NiJ9.' +
  btoa(JSON.stringify({ sub: 'test@test.com', exp: 1000000000 }))
    .replace(/=/g, '')
    .replace(/\+/g, '-')
    .replace(/\//g, '_') +
  '.signature';

describe('jwt utils', () => {
  it('decodes JWT payload without library', () => {
    const payload = decodeJwtPayload(FUTURE_TOKEN);
    expect(payload.sub).toBe('test@test.com');
    expect(payload.exp).toBe(9999999999);
  });

  it('returns empty object for invalid token', () => {
    expect(decodeJwtPayload('invalid')).toEqual({});
    expect(decodeJwtPayload('')).toEqual({});
  });

  it('getTokenExpiryMs returns expiry in milliseconds', () => {
    expect(getTokenExpiryMs(FUTURE_TOKEN)).toBe(9999999999 * 1000);
  });

  it('getTokenExpiryMs returns null for invalid token', () => {
    expect(getTokenExpiryMs('invalid')).toBeNull();
  });

  it('isTokenExpiringSoon returns false for far-future token', () => {
    expect(isTokenExpiringSoon(FUTURE_TOKEN)).toBe(false);
  });

  it('isTokenExpiringSoon returns true for expired token', () => {
    expect(isTokenExpiringSoon(PAST_TOKEN)).toBe(true);
  });

  it('isTokenExpiringSoon respects custom threshold', () => {
    // exp = 9999999999 → far future, even with huge threshold
    expect(isTokenExpiringSoon(FUTURE_TOKEN, 9999999998 * 1000)).toBe(true);
  });
});
