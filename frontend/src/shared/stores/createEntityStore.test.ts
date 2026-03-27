import { beforeEach, describe, expect, it, vi } from 'vitest';

import { httpClient } from '../api/http-client';

import { createEntityStore } from './createEntityStore';

vi.mock('../api/http-client', () => ({ httpClient: vi.fn() }));

describe('createEntityStore', () => {
  beforeEach(() => vi.clearAllMocks());

  it('fetches items and pagination data', async () => {
    const useStore = createEntityStore<{ id: string }>({ endpoint: '/items' });
    vi.mocked(httpClient).mockResolvedValue({
      items: [{ id: '1' }],
      total: 1,
      page: 2,
      total_pages: 3,
    });

    await useStore.getState().fetchItems(2, 10);

    expect(useStore.getState().items).toEqual([{ id: '1' }]);
    expect(useStore.getState().page).toBe(2);
    expect(useStore.getState().totalPages).toBe(3);
  });

  it('deletes items by id or _id without leaving isSaving stuck', async () => {
    const useStore = createEntityStore<{ id?: string; _id?: string }>({
      endpoint: '/items',
    });
    useStore.setState({ items: [{ id: '1' }, { _id: '2' }], total: 2 });
    vi.mocked(httpClient).mockResolvedValue({});

    await useStore.getState().deleteItem('2');

    expect(useStore.getState().items).toEqual([{ id: '1' }]);
    expect(useStore.getState().isSaving).toBe(false);
  });
});
