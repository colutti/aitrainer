import { ChevronRight, ChevronLeft, X, Play } from 'lucide-react';
import { useEffect, useState, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';

import { cn } from '../../utils/cn';

import { Button } from './Button';

export interface TourStep {
  targetId: string;
  titleKey: string;
  descriptionKey: string;
  imageUrl?: string;
}

interface IntroTourProps {
  steps: TourStep[];
  tourKey: string;
  onFinish?: () => void;
}

export function IntroTour({ steps, tourKey, onFinish }: IntroTourProps) {
  const { t } = useTranslation();
  const [currentStep, setCurrentStep] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [coords, setCoords] = useState<{ top: number; left: number; width: number; height: number; } | null>(null);
  
  const LOCAL_STORAGE_KEY = useMemo(() => `has_seen_tour_${tourKey}`, [tourKey]);

  useEffect(() => {
    const hasSeen = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!hasSeen) {
      setTimeout(() => { setIsOpen(true); }, 0);
    }
  }, [LOCAL_STORAGE_KEY]);

  const updateCoords = useCallback(() => {
    if (!isOpen || currentStep >= steps.length) return;
    
    const step = steps[currentStep] as TourStep | undefined;
    if (!step) return;
    
    const elements = Array.from(document.querySelectorAll(`[data-tour="${step.targetId}"]`));
    
    // Find the visible element (important for responsive UI like Sidebar vs BottomNav)
    const element = elements.find(el => {
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    });
    
    if (element) {
      const rect = element.getBoundingClientRect();
      setCoords({
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
        height: rect.height
      });
      
      // Scroll to element gently if it is not visible or just started
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
      // Keep old coords if element momentarily disappears, or null if never found
      setCoords(prev => prev);
    }
  }, [isOpen, currentStep, steps]);

  useEffect(() => {
    // Always attempt update immediately
    setTimeout(() => { updateCoords(); }, 0);

    // Poll a few times a second to handle async UI loading
    const intervalId = setInterval(() => {
        updateCoords();
    }, 500);

    window.addEventListener('resize', updateCoords);
    window.addEventListener('scroll', updateCoords);
    
    return () => { 
      clearInterval(intervalId);
      window.removeEventListener('resize', updateCoords); 
      window.removeEventListener('scroll', updateCoords); 
    };
  }, [updateCoords]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(s => s + 1);
    } else {
      handleFinish();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(s => s - 1);
    }
  };

  const handleFinish = () => {
    localStorage.setItem(LOCAL_STORAGE_KEY, 'true');
    setIsOpen(false);
    onFinish?.();
  };

  if (!isOpen) return null;

  return createPortal(
    <div className="fixed inset-0 z-9999 pointer-events-none overflow-hidden">
      {/* Overlay with Spotlight mask */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-[2px] pointer-events-auto transition-opacity duration-500"
        style={{
          clipPath: coords 
            ? `polygon(0% 0%, 0% 100%, ${coords.left.toString()}px 100%, ${coords.left.toString()}px ${coords.top.toString()}px, ${(coords.left + coords.width).toString()}px ${coords.top.toString()}px, ${(coords.left + coords.width).toString()}px ${(coords.top + coords.height).toString()}px, ${coords.left.toString()}px ${(coords.top + coords.height).toString()}px, ${coords.left.toString()}px 100%, 100% 100%, 100% 0%)`
            : 'none'
        }}
      />

      {/* Spotlight highlight border */}
      {coords && (
        <div 
          className="absolute border-2 border-gradient-start rounded-2xl shadow-[0_0_50px_rgba(249,115,22,0.5)] transition-all duration-500"
          style={{
            top: coords.top - 4,
            left: coords.left - 4,
            width: coords.width + 8,
            height: coords.height + 8
          }}
        />
      )}

      {/* Popover Card */}
      <div 
        className={cn(
          "absolute pointer-events-auto w-[340px] p-6 rounded-3xl bg-dark-card border border-border shadow-2xl transition-all duration-500",
          !coords ? "top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" : ""
        )}
        style={coords ? {
          top: coords.top + coords.height + 20 > window.innerHeight + window.scrollY - (steps[currentStep]?.imageUrl ? 460 : 300) 
               ? coords.top - (steps[currentStep]?.imageUrl ? 440 : 280) 
               : coords.top + coords.height + 20,
          left: Math.min(Math.max(20, coords.left + coords.width / 2 - 170), window.innerWidth - 360)
        } : {}}
      >
        <div className="flex justify-between items-start mb-4">
          <div className="p-2 rounded-xl bg-gradient-start/10 text-gradient-start font-bold text-xs uppercase tracking-widest flex items-center gap-2">
            <Play size={12} fill="currentColor" />
            Step {currentStep + 1} / {steps.length}
          </div>
          <button onClick={handleFinish} className="text-zinc-400 hover:text-white transition-colors p-1">
            <X size={20} />
          </button>
        </div>

        {steps[currentStep]?.imageUrl && (
          <div className="mb-5 rounded-2xl overflow-hidden shadow-lg border border-white/5 relative bg-dark-bg/50 pb-[56.25%]">
             <img 
               src={steps[currentStep].imageUrl} 
               alt="Step preview" 
               className="absolute inset-0 w-full h-full object-cover"
             />
             <div className="absolute inset-0 shadow-[inset_0_0_20px_rgba(0,0,0,0.5)] pointer-events-none" />
          </div>
        )}

        <h3 className="text-xl font-bold text-text-primary mb-2">
          {steps[currentStep] ? t(steps[currentStep].titleKey) : ''}
        </h3>
        <p className="text-sm text-text-secondary leading-relaxed mb-8">
          {steps[currentStep] ? t(steps[currentStep].descriptionKey) : ''}
        </p>

        <div className="flex items-center justify-between gap-4">
          <button 
            onClick={handleFinish}
            className="text-xs font-bold text-zinc-400 hover:text-white transition-colors underline decoration-dotted"
          >
            {t('dashboard.tour.skip')}
          </button>
          
          <div className="flex gap-2">
            {currentStep > 0 && (
              <Button variant="secondary" onClick={handleBack} className="p-2 w-10 h-10 rounded-xl">
                <ChevronLeft size={20} />
              </Button>
            )}
            <Button onClick={handleNext} className="flex-1 px-6 rounded-xl flex items-center justify-center gap-2 font-bold group">
              {currentStep === steps.length - 1 ? t('dashboard.tour.finish') : t('dashboard.tour.next')}
              <ChevronRight size={18} className="group-hover:translate-x-0.5 transition-transform" />
            </Button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
