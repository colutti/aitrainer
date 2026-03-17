import {
  Plus
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';

import { Button } from '../../../shared/components/ui/Button';
import { DataList } from '../../../shared/components/ui/DataList';
import type { WeightLog } from '../../../shared/types/body';
import { useWeightTab } from '../hooks/useWeightTab';

import { WeightLogCard } from './WeightLogCard';
import { WeightLogDrawer } from './WeightLogDrawer';

export function WeightTab() {
  const [viewLog, setViewLog] = useState<WeightLog | null>(null);
  const [isEntryDrawerOpen, setIsEntryDrawerOpen] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  const {
    history,
    isLoading,
    isSaving,
    register,
    control,
    handleSubmit,
    errors,
    deleteEntry,
    editEntry,
    cancelEdit,
    isEditing,
    editingDate,
    onSubmit,
    page,
    totalPages,
    changePage
  } = useWeightTab();
  const { t } = useTranslation();

  // Handle URL action trigger
  useEffect(() => {
    const action = searchParams.get('action');
    if (action === 'log-weight' && !isEntryDrawerOpen) {
      setTimeout(() => { setIsEntryDrawerOpen(true); }, 0);
    }
  }, [searchParams, isEntryDrawerOpen]);

  const handleCloseEntryDrawer = () => {
    setIsEntryDrawerOpen(false);
    if (isEditing) cancelEdit();
    // Remove search param if present
    if (searchParams.has('action')) {
      const newParams = new URLSearchParams(searchParams);
      newParams.delete('action');
      setSearchParams(newParams, { replace: true });
    }
  };

  const handleEdit = (log: WeightLog) => {
    editEntry(log);
    setIsEntryDrawerOpen(true);
  };

  if (isLoading && history.length === 0) {
    return (
      <div className="space-y-8">
        <div className="h-64 bg-dark-card rounded-xl border border-border" />
      </div>
    );
  }

  return (
    <div className="space-y-8 w-full overflow-x-hidden">
      {/* Header Action */}
      <div className="flex justify-end">
        <Button 
          variant="primary" 
          onClick={() => { setIsEntryDrawerOpen(true); }}
          className="shadow-orange gap-2 w-full md:w-auto"
          size="lg"
        >
          <Plus size={20} />
          {t('body.weight.register_title')}
        </Button>
      </div>

      <DataList
        title={t('body.weight.history_title')}
        data={history}
        isLoading={isLoading}
        renderItem={(log) => (
          <WeightLogCard 
            log={log} 
            onDelete={(date) => { void deleteEntry(date); }} 
            onEdit={handleEdit} 
            onClick={setViewLog}
          />
        )}
        keyExtractor={(item) => item.id ?? item.date}
        layout="list"
        emptyState={{
          title: t('body.weight.empty_title'),
          description: t('body.weight.empty_desc')
        }}
        pagination={{
            currentPage: page,
            totalPages: totalPages,
            onPageChange: (newPage) => { changePage(newPage); }
        }}
      />

      {/* Details Drawer */}
      <WeightLogDrawer 
        log={viewLog} 
        isOpen={!!viewLog} 
        onClose={() => { setViewLog(null); }} 
        mode="view"
      />

      {/* Entry/Edit Drawer */}
      <WeightLogDrawer 
        log={isEditing ? history.find(l => l.date === editingDate) ?? null : null} 
        isOpen={isEntryDrawerOpen} 
        onClose={handleCloseEntryDrawer}
        mode="edit"
        register={register}
        control={control}
        errors={errors}
        isSaving={isSaving}
        handleSubmit={handleSubmit}
        onSubmit={async (data) => { 
           await onSubmit(data);
           setIsEntryDrawerOpen(false); 
        }}
        onCancelEdit={handleCloseEntryDrawer}
      />
    </div>
  );
}
