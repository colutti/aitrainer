import {
  History,
  Plus
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useSearchParams } from 'react-router-dom';

import { Button } from '../../../shared/components/ui/Button';
import { DataList } from '../../../shared/components/ui/DataList';
import { type NutritionLog } from '../../../shared/types/nutrition';
import { NutritionLogCard } from '../../nutrition/components/NutritionLogCard';
import { useNutritionTab } from '../hooks/useNutritionTab';

import { NutritionLogDrawer } from './NutritionLogDrawer';

export function NutritionTab() {
  const [viewLog, setViewLog] = useState<NutritionLog | null>(null);
  const [isEntryDrawerOpen, setIsEntryDrawerOpen] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  const {
    logs,
    isLoading,
    isSaving,
    currentPage,
    totalPages,
    register,
    control,
    handleSubmit,
    errors,
    deleteEntry,
    editEntry,
    cancelEdit,
    isEditing,
    editingId,
    onSubmit,
    changePage
  } = useNutritionTab();
  const { t } = useTranslation();

  // Handle URL action trigger
  useEffect(() => {
    const action = searchParams.get('action');
    if (action === 'log-meal' && !isEntryDrawerOpen) {
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

  const handleEdit = (log: NutritionLog) => {
    editEntry(log);
    setIsEntryDrawerOpen(true);
  };

  if (isLoading && logs.length === 0) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-64 bg-dark-card rounded-2xl" />
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
          {t('body.nutrition.register_title')}
        </Button>
      </div>

      <DataList
        title={
          <div className="flex items-center gap-2">
            <History className="text-gradient-start" size={24} />
            <span>{t('body.nutrition.history_title')}</span>
          </div>
        }
        data={logs}
        isLoading={isLoading}
        renderItem={(log: NutritionLog) => (
          <NutritionLogCard 
            log={log} 
            onDelete={(id) => { void deleteEntry(id); }} 
            onEdit={handleEdit}
            onClick={setViewLog}
          />
        )}
        keyExtractor={(item: NutritionLog) => item.id}
        layout="list"
        emptyState={{
          title: t('body.nutrition.empty_title'),
          description: t('body.nutrition.empty_desc')
        }}
        pagination={{
          currentPage: currentPage,
          totalPages: totalPages,
          onPageChange: (newPage: number) => { changePage(newPage); }
        }}
      />

      {/* Details Drawer */}
      <NutritionLogDrawer
        log={viewLog}
        isOpen={!!viewLog}
        onClose={() => { setViewLog(null); }}
        mode="view"
      />

      {/* Entry/Edit Drawer */}
      <NutritionLogDrawer
        log={isEditing ? logs.find(l => l.id === editingId) ?? null : null}
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
