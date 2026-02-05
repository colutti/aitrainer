/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/require-await */
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from './http-client';

describe('httpClient', () => {
  beforeEach(() => {
    // Clear all mocks
    vi.clearAllMocks();
  });

  describe('Authentication', () => {
    it('should attach Bearer token when token exists in localStorage', async () => {
      const mockToken = 'test-jwt-token';
      localStorage.setItem('auth_token', mockToken);

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
      });

      await httpClient('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: `Bearer ${mockToken}`,
          }),
        })
      );
    });

    it('should make request without token when not authenticated', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
      });

      await httpClient('/test');

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.anything(),
          }),
        })
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle 401 error and clear token', async () => {
      localStorage.setItem('auth_token', 'expired-token');

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      });

      await expect(httpClient('/test')).rejects.toThrow('Unauthorized');
      expect(localStorage.getItem('auth_token')).toBeNull();
    });

    it('should handle 429 error (too many requests)', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({ detail: 'Too many requests' }),
      });

      await expect(httpClient('/test')).rejects.toThrow('Too many requests');
    });

    it('should handle 5xx server errors', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      });

      await expect(httpClient('/test')).rejects.toThrow('Internal server error');
    });

    it('should handle network errors', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
        new Error('Network error')
      );

      await expect(httpClient('/test')).rejects.toThrow('Network error');
    });
  });

  describe('Request Configuration', () => {
    it('should send POST request with JSON body', async () => {
      const testData = { name: 'test' };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      await httpClient('/test', {
        method: 'POST',
        body: JSON.stringify(testData),
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: JSON.stringify(testData),
        })
      );
    });

    it('should merge custom headers with default headers', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ data: 'test' }),
      });

      await httpClient('/test', {
        headers: {
          'X-Custom-Header': 'custom-value',
        },
      });

      expect(global.fetch).toHaveBeenCalledWith(
        '/api/test',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Custom-Header': 'custom-value',
          }),
        })
      );
    });
  });

  describe('Response Handling', () => {
    it('should return parsed JSON response', async () => {
      const mockResponse = { data: 'test', id: 123 };

      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await httpClient('/test');

      expect(result).toEqual(mockResponse);
    });

    it('should handle empty response body', async () => {
      (global.fetch as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => {
          throw new Error('No content');
        },
      });

      const result = await httpClient('/test');

      expect(result).toBeUndefined();
    });
  });
});
