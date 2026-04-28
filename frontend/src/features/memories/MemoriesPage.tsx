import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

import { EntityListScreen } from '../../shared/components/layout/EntityListScreen';
import { useConfirmation } from '../../shared/hooks/useConfirmation';
import { useDemoMode } from '../../shared/hooks/useDemoMode';
import { useMemoryStore } from '../../shared/hooks/useMemory';
import { useNotificationStore } from '../../shared/hooks/useNotification';

import { MemoriesView } from './components/MemoriesView';

/**
 * MemoriesPage component (Container)
 * 
 * Manages the fetching and deletion of AI-learned "memories".
 * Delegates rendering to MemoriesView.
 */
export default function MemoriesPage() {
  const { 
    memories, 
    isLoading, 
    currentPage, 
    totalPages, 
    totalMemories,
    fetchMemories, 
    nextPage, 
    previousPage, 
    deleteMemory 
  } = useMemoryStore();

  const { confirm } = useConfirmation();
  const notify = useNotificationStore();
  const { t } = useTranslation();
  const { isReadOnly: isDemoUser } = useDemoMode();

  useEffect(() => {
    void fetchMemories();
  }, [fetchMemories]);

  const handleDelete = async (memoryId: string) => {
    if (isDemoUser) return;
    const isConfirmed = await confirm({
      title: t('memories.delete_confirm_title'),
      message: t('memories.delete_confirm_message'),
      confirmText: t('memories.delete_confirm_btn'),
      type: 'danger'
    });

    if (isConfirmed) {
      try {
        await deleteMemory(memoryId);
        notify.success(t('memories.delete_success'));
      } catch {
        notify.error(t('memories.delete_error'));
      }
    }
  };

  return (
    <div data-testid="memories-list-screen">
      <EntityListScreen
        title={t('memories.title')}
        subtitle={t('memories.subtitle')}
        list={
          <MemoriesView
            memories={memories}
            isLoading={isLoading}
            totalMemories={totalMemories}
            currentPage={currentPage}
            totalPages={totalPages}
            isReadOnly={isDemoUser}
            onDelete={(id) => { void handleDelete(id); }}
            onPageChange={(page) => {
              if (page > currentPage) void nextPage();
              else if (page < currentPage) void previousPage();
            }}
          />
        }
      />
    </div>
  );
}
