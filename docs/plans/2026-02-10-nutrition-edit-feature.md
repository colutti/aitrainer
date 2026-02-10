# Nutrition Edit Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the nutrition edit feature so the date field is properly populated when editing a record, and allow users to update their nutrition logs.

**Architecture:** Add an `updateLog` method to the Zustand store, create a modal component with a form for editing nutrition logs, integrate the edit modal into NutritionPage with proper date handling, and add backend support for updates.

**Tech Stack:** React 19, TypeScript, Zustand (state management), React Hook Form, Zod (validation), FastAPI (backend), TailwindCSS

---

## Task 1: Add updateLog Action to useNutritionStore

**Files:**
- Modify: `frontend/src/shared/hooks/useNutrition.ts` (line 21-27 and 85-101)
- Modify: `frontend/src/shared/types/nutrition.ts`

**Step 1: Add UpdateNutritionLogRequest type**

Read the nutrition types file to understand the structure:

```bash
cat frontend/src/shared/types/nutrition.ts
```

Then add the update type after CreateNutritionLogRequest (around line 20):

```typescript
export interface UpdateNutritionLogRequest {
  date: string; // ISO date string
  calories: number;
  protein_grams: number;
  carbs_grams: number;
  fat_grams: number;
  meal_name?: string;
  notes?: string;
}
```

**Step 2: Add updateLog method to store interface**

In `useNutrition.ts`, add to `NutritionActions` interface (after line 25):

```typescript
updateLog: (id: string, data: UpdateNutritionLogRequest) => Promise<void>;
```

**Step 3: Import the new type**

Update imports at top of `useNutrition.ts`:

```typescript
import type {
  NutritionListResponse,
  NutritionLog,
  NutritionStats,
  CreateNutritionLogRequest,
  UpdateNutritionLogRequest  // Add this
} from '../types/nutrition';
```

**Step 4: Implement updateLog method in store**

Add after the `deleteLog` method (after line 124):

```typescript
updateLog: async (id: string, data: UpdateNutritionLogRequest) => {
  set({ isLoading: true, error: null });
  try {
    await httpClient<NutritionLog>(`/nutrition/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    await Promise.all([get().fetchLogs(), get().fetchStats()]);
  } catch (error) {
    console.error('Error updating nutrition log:', error);
    set({
      isLoading: false,
      error: 'Falha ao atualizar registro nutricional.'
    });
    throw error;
  }
},
```

**Step 5: Run type check**

```bash
cd frontend && npm run type-check
```

Expected: No TypeScript errors

**Step 6: Commit**

```bash
git add frontend/src/shared/hooks/useNutrition.ts frontend/src/shared/types/nutrition.ts
git commit -m "feat: add updateLog method to nutrition store"
```

---

## Task 2: Create NutritionEditModal Component

**Files:**
- Create: `frontend/src/features/nutrition/components/NutritionEditModal.tsx`
- Create: `frontend/src/features/nutrition/components/NutritionEditModal.test.tsx`

**Step 1: Create the modal component**

Create `frontend/src/features/nutrition/components/NutritionEditModal.tsx`:

```typescript
import { X } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

import { Button } from '../../../shared/components/ui/Button';
import { Modal } from '../../../shared/components/ui/Modal';
import { Input } from '../../../shared/components/ui/Input';
import { type NutritionLog } from '../../../shared/types/nutrition';
import { formatDate } from '../../../shared/utils/format-date';

const editNutritionSchema = z.object({
  date: z.string().min(1, 'Data é obrigatória'),
  meal_name: z.string().optional(),
  calories: z.number().min(0, 'Calorias devem ser >= 0'),
  protein_grams: z.number().min(0, 'Proteína devem ser >= 0'),
  carbs_grams: z.number().min(0, 'Carboidratos devem ser >= 0'),
  fat_grams: z.number().min(0, 'Gordura devem ser >= 0'),
  notes: z.string().optional(),
});

type EditNutritionFormData = z.infer<typeof editNutritionSchema>;

interface NutritionEditModalProps {
  log: NutritionLog | null;
  isOpen: boolean;
  isLoading?: boolean;
  onClose: () => void;
  onSave: (data: EditNutritionFormData) => Promise<void>;
}

/**
 * Modal for editing nutrition logs
 * Allows updating date, macros, and meal details
 */
export function NutritionEditModal({
  log,
  isOpen,
  isLoading = false,
  onClose,
  onSave,
}: NutritionEditModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<EditNutritionFormData>({
    resolver: zodResolver(editNutritionSchema),
    defaultValues: {
      date: '',
      calories: 0,
      protein_grams: 0,
      carbs_grams: 0,
      fat_grams: 0,
      meal_name: '',
      notes: '',
    },
  });

  // Reset form when log changes
  useEffect(() => {
    if (log && isOpen) {
      const dateStr = log.date instanceof Date
        ? log.date.toISOString().split('T')[0]
        : new Date(log.date).toISOString().split('T')[0];

      reset({
        date: dateStr,
        meal_name: log.meal_name || '',
        calories: log.calories,
        protein_grams: log.protein_grams,
        carbs_grams: log.carbs_grams,
        fat_grams: log.fat_grams,
        notes: log.notes || '',
      });
    }
  }, [log, isOpen, reset]);

  const onSubmit = async (data: EditNutritionFormData) => {
    try {
      await onSave(data);
      onClose();
    } catch {
      // Error is handled in the parent component
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="bg-dark-card border border-border rounded-2xl p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-text-primary">Editar Registro</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded-lg transition-colors"
          >
            <X size={20} className="text-text-muted" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* Date Field */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Data
            </label>
            <input
              type="date"
              {...register('date')}
              className="w-full px-4 py-2 bg-dark-bg border border-border rounded-lg text-text-primary focus:outline-none focus:border-gradient-start"
            />
            {errors.date && (
              <p className="text-red-500 text-sm mt-1">{errors.date.message}</p>
            )}
          </div>

          {/* Meal Name */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Refeição (opcional)
            </label>
            <input
              type="text"
              placeholder="Ex: Café da manhã, Almoço..."
              {...register('meal_name')}
              className="w-full px-4 py-2 bg-dark-bg border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-gradient-start"
            />
          </div>

          {/* Calories */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Calorias (kcal)
            </label>
            <input
              type="number"
              step="0.1"
              {...register('calories', { valueAsNumber: true })}
              className="w-full px-4 py-2 bg-dark-bg border border-border rounded-lg text-text-primary focus:outline-none focus:border-gradient-start"
            />
            {errors.calories && (
              <p className="text-red-500 text-sm mt-1">{errors.calories.message}</p>
            )}
          </div>

          {/* Macros Grid */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Proteína (g)
              </label>
              <input
                type="number"
                step="0.1"
                {...register('protein_grams', { valueAsNumber: true })}
                className="w-full px-3 py-2 bg-dark-bg border border-border rounded-lg text-text-primary focus:outline-none focus:border-gradient-start text-sm"
              />
              {errors.protein_grams && (
                <p className="text-red-500 text-xs mt-1">
                  {errors.protein_grams.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Carbs (g)
              </label>
              <input
                type="number"
                step="0.1"
                {...register('carbs_grams', { valueAsNumber: true })}
                className="w-full px-3 py-2 bg-dark-bg border border-border rounded-lg text-text-primary focus:outline-none focus:border-gradient-start text-sm"
              />
              {errors.carbs_grams && (
                <p className="text-red-500 text-xs mt-1">
                  {errors.carbs_grams.message}
                </p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Gordura (g)
              </label>
              <input
                type="number"
                step="0.1"
                {...register('fat_grams', { valueAsNumber: true })}
                className="w-full px-3 py-2 bg-dark-bg border border-border rounded-lg text-text-primary focus:outline-none focus:border-gradient-start text-sm"
              />
              {errors.fat_grams && (
                <p className="text-red-500 text-xs mt-1">
                  {errors.fat_grams.message}
                </p>
              )}
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Anotações (opcional)
            </label>
            <textarea
              placeholder="Anotações..."
              {...register('notes')}
              rows={3}
              className="w-full px-4 py-2 bg-dark-bg border border-border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:border-gradient-start resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              disabled={isSubmitting || isLoading}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isSubmitting || isLoading}
              className="flex-1"
            >
              {isSubmitting || isLoading ? 'Salvando...' : 'Salvar'}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
```

**Step 2: Check if Modal component exists**

```bash
ls -la frontend/src/shared/components/ui/Modal.tsx
```

If it doesn't exist, we'll create it in Task 3.

**Step 3: Create basic test file**

Create `frontend/src/features/nutrition/components/NutritionEditModal.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NutritionEditModal } from './NutritionEditModal';
import type { NutritionLog } from '../../../shared/types/nutrition';

describe('NutritionEditModal', () => {
  const mockLog: NutritionLog = {
    id: '1',
    date: '2026-02-10',
    calories: 2000,
    protein_grams: 150,
    carbs_grams: 200,
    fat_grams: 70,
    meal_name: 'Almoço',
    notes: 'Test note',
  };

  it('renders modal when isOpen is true', () => {
    const onClose = vi.fn();
    const onSave = vi.fn();

    render(
      <NutritionEditModal
        log={mockLog}
        isOpen={true}
        onClose={onClose}
        onSave={onSave}
      />
    );

    expect(screen.getByText('Editar Registro')).toBeInTheDocument();
  });

  it('does not render modal when isOpen is false', () => {
    const onClose = vi.fn();
    const onSave = vi.fn();

    render(
      <NutritionEditModal
        log={mockLog}
        isOpen={false}
        onClose={onClose}
        onSave={onSave}
      />
    );

    expect(screen.queryByText('Editar Registro')).not.toBeInTheDocument();
  });
});
```

**Step 4: Run type check**

```bash
cd frontend && npm run type-check
```

Expected: May have errors if Modal doesn't exist (we'll fix in Task 3)

**Step 5: Commit**

```bash
git add frontend/src/features/nutrition/components/NutritionEditModal.tsx frontend/src/features/nutrition/components/NutritionEditModal.test.tsx
git commit -m "feat: create NutritionEditModal component"
```

---

## Task 3: Create Modal UI Component (if missing)

**Files:**
- Create: `frontend/src/shared/components/ui/Modal.tsx`

**Step 1: Check if Modal exists**

```bash
ls -la frontend/src/shared/components/ui/Modal.tsx 2>&1
```

**Step 2: If it doesn't exist, create it**

Create `frontend/src/shared/components/ui/Modal.tsx`:

```typescript
import { useEffect } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
}

/**
 * Modal component with backdrop
 * Renders children in a portal to avoid stacking context issues
 */
export function Modal({ isOpen, onClose, children }: ModalProps) {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>,
    document.body
  );
}
```

**Step 3: Run type check**

```bash
cd frontend && npm run type-check
```

Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/shared/components/ui/Modal.tsx
git commit -m "feat: create Modal UI component"
```

---

## Task 4: Integrate Edit Modal into NutritionPage

**Files:**
- Modify: `frontend/src/features/nutrition/NutritionPage.tsx`

**Step 1: Add state and imports**

Add to imports (after line 22):

```typescript
import { useState } from 'react';
import { NutritionEditModal } from './components/NutritionEditModal';
```

**Step 2: Add modal state in component**

Inside `NutritionPage` function, after line 42 (after `const notify = ...`), add:

```typescript
const [editingLog, setEditingLog] = useState<NutritionLog | null>(null);
const [isEditModalOpen, setIsEditModalOpen] = useState(false);
```

**Step 3: Add handleEdit function**

After the `handleDelete` function (after line 66), add:

```typescript
const handleEdit = (log: NutritionLog) => {
  setEditingLog(log);
  setIsEditModalOpen(true);
};

const handleSaveEdit = async (data: {
  date: string;
  calories: number;
  protein_grams: number;
  carbs_grams: number;
  fat_grams: number;
  meal_name?: string;
  notes?: string;
}) => {
  if (!editingLog) return;

  try {
    await updateLog(editingLog.id, data);
    notify.success('Registro atualizado com sucesso!');
  } catch {
    notify.error('Erro ao atualizar registro.');
  }
};
```

**Step 4: Add updateLog to the destructured store**

Change line 31-40 to include `updateLog`:

```typescript
const {
  logs,
  stats,
  isLoading,
  fetchLogs,
  fetchStats,
  deleteLog,
  updateLog,  // Add this
  page,
  totalPages
} = useNutritionStore();
```

**Step 5: Pass onEdit callback to NutritionLogCard**

Change lines 148-153 to:

```typescript
<NutritionLogCard
  log={log}
  onEdit={handleEdit}
  onDelete={(id) => {
    void handleDelete(id);
  }}
/>
```

**Step 6: Add modal to JSX**

Before the closing `</div>` of the component (before line 238), add:

```typescript
<NutritionEditModal
  log={editingLog}
  isOpen={isEditModalOpen}
  isLoading={isLoading}
  onClose={() => {
    setIsEditModalOpen(false);
    setEditingLog(null);
  }}
  onSave={handleSaveEdit}
/>
```

**Step 7: Run type check**

```bash
cd frontend && npm run type-check
```

Expected: No errors

**Step 8: Run tests**

```bash
cd frontend && npm test -- --run NutritionPage
```

Expected: Tests pass

**Step 9: Commit**

```bash
git add frontend/src/features/nutrition/NutritionPage.tsx
git commit -m "feat: integrate edit modal into NutritionPage with date handling"
```

---

## Task 5: Add Backend API Endpoint for Update

**Files:**
- Modify: `backend/src/api/endpoints/nutrition.py`

**Step 1: Check existing nutrition endpoint structure**

```bash
cat backend/src/api/endpoints/nutrition.py | head -50
```

**Step 2: Add PUT endpoint for updating nutrition log**

Find the delete endpoint and add after it:

```python
@router.put("/{log_id}", response_model=NutritionLog)
async def update_nutrition_log(
    log_id: str,
    log_data: CreateNutritionLogRequest,
    current_user: User = Depends(get_current_user),
    nutrition_service: NutritionService = Depends(get_nutrition_service),
):
    """Update an existing nutrition log."""
    try:
        updated_log = await nutrition_service.update_log(
            user_id=current_user.id,
            log_id=log_id,
            data=log_data,
        )
        return updated_log
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating nutrition log: {e}")
        raise HTTPException(status_code=500, detail="Failed to update nutrition log")
```

**Step 3: Add update_log method to NutritionService**

Find the service file:

```bash
find backend/src/services -name "*nutrition*"
```

Add the method to the service class:

```python
async def update_log(
    self,
    user_id: str,
    log_id: str,
    data: CreateNutritionLogRequest,
) -> NutritionLog:
    """Update a nutrition log."""
    # Verify ownership
    existing = await self.repository.find_by_id(log_id)
    if not existing or existing.get("user_id") != user_id:
        raise ValueError("Nutrition log not found")

    # Update document
    updated_log = await self.repository.update(
        log_id,
        {
            "date": data.date,
            "calories": data.calories,
            "protein_grams": data.protein_grams,
            "carbs_grams": data.carbs_grams,
            "fat_grams": data.fat_grams,
            "meal_name": data.meal_name,
            "notes": data.notes,
        }
    )

    return NutritionLog(**updated_log)
```

**Step 4: Run type check on backend**

```bash
cd backend && python -m py_compile src/api/endpoints/nutrition.py
```

Expected: No syntax errors

**Step 5: Run backend tests**

```bash
cd backend && pytest tests/ -k nutrition -v
```

Expected: Tests pass

**Step 6: Commit**

```bash
git add backend/src/api/endpoints/nutrition.py backend/src/services/*.py
git commit -m "feat: add PUT endpoint for updating nutrition logs"
```

---

## Task 6: Test the Full Feature

**Files:**
- Manual testing

**Step 1: Start the application**

```bash
make up
```

Wait for services to start (10-15 seconds)

**Step 2: Test edit flow**

1. Navigate to Nutrição page
2. Click edit button on a nutrition log
3. Modal should open with all fields populated including date
4. Change the date and some macro values
5. Click "Salvar"
6. Verify the log is updated without page refresh

**Step 3: Verify date field is populated**

Open browser DevTools, check that the date input field has a value when modal opens.

**Step 4: Test error handling**

1. Try to submit with invalid date (clear the field)
2. Verify error message appears
3. Try to submit with negative calories
4. Verify validation error appears

**Step 5: Commit (if manual testing passes)**

```bash
git add frontend/ backend/
git commit -m "test: verify nutrition edit feature works end-to-end"
```

---

## Summary

This plan implements the complete nutrition edit feature:
- ✅ Zustand store with `updateLog` action
- ✅ Modal component for editing
- ✅ Form with proper date field handling
- ✅ Integration with NutritionPage
- ✅ Backend API support
- ✅ Validation and error handling

All fields, especially the date field, will be properly populated from the existing log data.
