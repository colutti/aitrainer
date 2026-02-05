/* eslint-disable @typescript-eslint/no-unnecessary-condition */
/* eslint-disable @typescript-eslint/await-thenable */
import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { useConfirmationStore } from './useConfirmation';

describe('useConfirmation', () => {
  beforeEach(() => {
    // Reset store state
    act(() => {
      useConfirmationStore.setState({
        isOpen: false,
        message: '',
        resolve: null,
      });
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useConfirmationStore());

      expect(result.current.isOpen).toBe(false);
      expect(result.current.message).toBe('');
    });
  });

  describe('confirm', () => {
    it('should return Promise that resolves true when accepted', async () => {
      const { result } = renderHook(() => useConfirmationStore());

      let confirmPromise: Promise<boolean> | null = null;

      act(() => {
        confirmPromise = result.current.confirm('Are you sure?');
      });

      // Modal should be open with the message
      expect(result.current.isOpen).toBe(true);
      expect(result.current.message).toBe('Are you sure?');

      // Accept the confirmation
      act(() => {
        result.current.accept();
      });

      if (!confirmPromise) {
        throw new Error('Promise should be defined');
      }

      const confirmed = await confirmPromise;

      expect(confirmed).toBe(true);
      expect(result.current.isOpen).toBe(false);
    });

    it('should return Promise that resolves false when cancelled', async () => {
      const { result } = renderHook(() => useConfirmationStore());

      let confirmPromise: Promise<boolean> | null = null;

      act(() => {
        confirmPromise = result.current.confirm('Delete this item?');
      });

      // Modal should be open
      expect(result.current.isOpen).toBe(true);
      expect(result.current.message).toBe('Delete this item?');

      // Cancel the confirmation
      act(() => {
        result.current.cancel();
      });

      if (!confirmPromise) {
        throw new Error('Promise should be defined');
      }

      const confirmed = await confirmPromise;

      expect(confirmed).toBe(false);
      expect(result.current.isOpen).toBe(false);
    });

    it('should handle multiple sequential confirmations', async () => {
      const { result } = renderHook(() => useConfirmationStore());

      // First confirmation - accept
      let confirm1: Promise<boolean> | null = null;
      act(() => {
        confirm1 = result.current.confirm('First confirmation');
      });
      act(() => {
        result.current.accept();
      });
      if (!confirm1) throw new Error('Promise should be defined');
      expect(await confirm1).toBe(true);

      // Second confirmation - cancel
      let confirm2: Promise<boolean> | null = null;
      act(() => {
        confirm2 = result.current.confirm('Second confirmation');
      });
      act(() => {
        result.current.cancel();
      });
      if (!confirm2) throw new Error('Promise should be defined');
      expect(await confirm2).toBe(false);

      // Third confirmation - accept
      let confirm3: Promise<boolean> | null = null;
      act(() => {
        confirm3 = result.current.confirm('Third confirmation');
      });
      act(() => {
        result.current.accept();
      });
      if (!confirm3) throw new Error('Promise should be defined');
      expect(await confirm3).toBe(true);
    });
  });

  describe('accept', () => {
    it('should close modal and resolve promise with true', async () => {
      const { result } = renderHook(() => useConfirmationStore());

      let confirmPromise: Promise<boolean> | null = null;

      act(() => {
        confirmPromise = result.current.confirm('Test message');
      });

      act(() => {
        result.current.accept();
      });

      if (!confirmPromise) {
        throw new Error('Promise should be defined');
      }

      expect(result.current.isOpen).toBe(false);
      expect(await confirmPromise).toBe(true);
    });
  });

  describe('cancel', () => {
    it('should close modal and resolve promise with false', async () => {
      const { result } = renderHook(() => useConfirmationStore());

      let confirmPromise: Promise<boolean> | null = null;

      act(() => {
        confirmPromise = result.current.confirm('Test message');
      });

      act(() => {
        result.current.cancel();
      });

      if (!confirmPromise) {
        throw new Error('Promise should be defined');
      }

      expect(result.current.isOpen).toBe(false);
      expect(await confirmPromise).toBe(false);
    });
  });
});
