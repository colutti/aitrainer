interface JwtPayload {
  exp?: number;
  sub?: string;
}

/**
 * Decodes the payload of a JWT token without verifying the signature.
 * Signature verification happens on the backend.
 */
export function decodeJwtPayload(token: string): JwtPayload {
  try {
    const parts = token.split('.');
    if (parts.length !== 3 || !parts[1]) return {};
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64)) as JwtPayload;
  } catch {
    return {};
  }
}

/** Returns the token expiry as a Unix timestamp in milliseconds, or null. */
export function getTokenExpiryMs(token: string): number | null {
  const { exp } = decodeJwtPayload(token);
  return exp !== undefined ? exp * 1000 : null;
}

/**
 * Returns true if the token expires within `thresholdMs` milliseconds.
 * Default threshold: 5 minutes.
 */
export function isTokenExpiringSoon(
  token: string,
  thresholdMs = 5 * 60 * 1000
): boolean {
  const expiryMs = getTokenExpiryMs(token);
  if (expiryMs === null) return false;
  return Date.now() >= expiryMs - thresholdMs;
}
