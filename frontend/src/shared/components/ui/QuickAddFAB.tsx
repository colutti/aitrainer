import { Plus, Scale, Utensils } from 'lucide-react';
import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { cn } from '../../utils/cn';

interface QuickAction {
  id: string;
  labelKey: string;
  icon: React.ElementType;
  onClick: () => void;
  color: string;
}

export function QuickAddFAB() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const ACTIONS: QuickAction[] = [
    {
      id: 'weight',
      labelKey: 'body.weight.register_title',
      icon: Scale,
      onClick: () => { void navigate('/dashboard/body/weight?action=log-weight'); },
      color: 'bg-emerald-500 hover:bg-emerald-400'
    },
    {
      id: 'meal',
      labelKey: 'body.nutrition.register_title',
      icon: Utensils,
      onClick: () => { void navigate('/dashboard/body/nutrition?action=log-meal'); },
      color: 'bg-orange-500 hover:bg-orange-400'
    }
  ];

  return (
    <div className="fixed bottom-24 right-6 md:bottom-12 md:right-12 z-100 flex flex-col items-end gap-3 pointer-events-none">
      {/* Backdrop when open */}
      <div 
        className={cn(
          "fixed inset-0 bg-black/40 backdrop-blur-sm z-[-1] transition-all duration-300 pointer-events-auto cursor-pointer",
          isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={() => { setIsOpen(false); }}
      />

      {/* Action Buttons */}
      <div className={cn(
        "flex flex-col-reverse items-end gap-3 transition-all duration-300",
        isOpen ? "translate-y-0 opacity-100 scale-100" : "translate-y-[20%] opacity-0 scale-95 pointer-events-none"
      )}>
        {ACTIONS.map((action, idx) => (
          <div 
            key={action.id} 
            className="flex items-center gap-3 transition-transform pointer-events-auto"
            style={{ transitionDelay: `${(idx * 40).toString()}ms` }}
          >
            <span className="px-3 py-1.5 rounded-xl bg-dark-card border border-border text-xs font-bold text-text-primary shadow-xl">
              {t(action.labelKey)}
            </span>
            <button
              onClick={() => { action.onClick(); setIsOpen(false); }}
              className={cn(
                "w-12 h-12 rounded-2xl flex items-center justify-center text-white shadow-2xl transition-all active:scale-95 group",
                action.color
              )}
            >
              <action.icon size={22} className="group-hover:scale-110 transition-transform" />
            </button>
          </div>
        ))}
      </div>

      {/* Main FAB */}
      <button
        onClick={() => { setIsOpen(!isOpen); }}
        className={cn(
          "w-16 h-16 rounded-3xl flex items-center justify-center shadow-[0_20px_50px_rgba(249,115,22,0.4)] pointer-events-auto transition-all active:scale-90",
          isOpen 
            ? "bg-zinc-800 text-text-primary rotate-45 border border-zinc-700" 
            : "bg-gradient-start text-white border border-white/20"
        )}
      >
        <Plus size={32} />
      </button>
    </div>
  );
}
