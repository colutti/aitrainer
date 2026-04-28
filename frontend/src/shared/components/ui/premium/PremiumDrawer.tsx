import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { type ReactNode, useEffect } from 'react';

import { cn } from '../../../utils/cn';
import { Button } from '../Button';

interface PremiumDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}

/**
 * Standardized Drawer component.
 * Handles transitions and accessibility.
 */
export function PremiumDrawer({ 
  isOpen, 
  onClose, 
  title, 
  subtitle, 
  icon, 
  children,
  className 
}: PremiumDrawerProps) {
  
  // Close on Escape key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) window.addEventListener('keydown', handleEsc);
    return () => { window.removeEventListener('keydown', handleEsc); };
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* BACKDROP */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 z-[100] cursor-pointer"
          />

          {/* DRAWER CONTENT */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={cn(
              "fixed right-0 top-0 h-full w-full md:w-[500px] bg-[color:var(--color-surface-container)] border-l border-[color:var(--color-outline-variant)] z-[101] shadow-2xl flex flex-col",
              className
            )}
          >
            {/* STICKY HEADER */}
            <header className="sticky top-0 bg-[color:var(--color-surface-container)] border-b border-[color:var(--color-outline-variant)] p-6 flex items-center justify-between z-10">
              <div className="flex items-center gap-4">
                {icon && (
                  <div className="w-12 h-12 rounded-2xl bg-[color:var(--color-surface-container-low)] border border-[color:var(--color-outline-variant)] flex items-center justify-center text-[color:var(--color-primary)]">
                    {icon}
                  </div>
                )}
                <div>
                  <h2 className="text-xl font-black text-[color:var(--color-on-surface)] tracking-tight">{title}</h2>
                  {subtitle && <p className="text-xs text-[color:var(--color-on-surface-variant)] font-bold uppercase tracking-widest">{subtitle}</p>}
                </div>
              </div>
              
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="p-2.5 rounded-xl bg-[color:var(--color-surface-container-low)] text-[color:var(--color-on-surface-variant)] hover:text-[color:var(--color-on-surface)] hover:bg-[color:var(--color-surface-container-high)] transition-all"
              >
                <X size={20} />
              </Button>
            </header>

            {/* SCROLLABLE BODY */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
              {children}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
