
import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { useConfirmationStore } from './useConfirmation';

describe('useConfirmation', () => {
  beforeEach(() => {
    // Reset store state
    act(() => {
      useConfirmationStore.getState().reset();
    });
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const { result } = renderHook(() => useConfirmationStore());

      expect(result.current.isOpen).toBe(false);
      expect(result.current.options.message).toBe('');
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
      expect(result.current.options.message).toBe('Are you sure?');

      // Accept the confirmation
      act(() => {
        result.current.accept();
      });

       
      if (!confirmPromise) {
        throw new Error('Promise should be defined');
      }

      const confirmed = await (confirmPromise as Promise<boolean>);

      expect(confirmed).toBe(true);
      expect(result.current.isOpen).toBe(false);
    });

    it('should handle options object', () => {
      const { result } = renderHook(() => useConfirmationStore());

      act(() => {
        void result.current.confirm({
          title: 'Custom Title',
          message: 'Custom Message',
          type: 'danger'
        });
      });

      expect(result.current.isOpen).toBe(true);
      expect(result.current.options.title).toBe('Custom Title');
      expect(result.current.options.message).toBe('Custom Message');
      expect(result.current.options.type).toBe('danger');
    });

    it('should return Promise that resolves false when cancelled', async () => {
      const { result } = renderHook(() => useConfirmationStore());

      let confirmPromise: Promise<boolean> | null = null;

      act(() => {
        confirmPromise = result.current.confirm('Delete this item?');
      });

      // Modal should be open
      expect(result.current.isOpen).toBe(true);
      expect(result.current.options.message).toBe('Delete this item?');

      // Cancel the confirmation
      act(() => {
        result.current.cancel();
      });

       
      if (!confirmPromise) {
        throw new Error('Promise should be defined');
      }

      const confirmed = await (confirmPromise as Promise<boolean>);

      expect(confirmed).toBe(false);
      expect(result.current.isOpen).toBe(false);
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
      expect(await (confirmPromise as Promise<boolean>)).toBe(true);
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
      expect(await (confirmPromise as Promise<boolean>)).toBe(false);
    });
  });
});
