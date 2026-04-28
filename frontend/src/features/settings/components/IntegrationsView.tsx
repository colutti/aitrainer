import { 
  Dumbbell, 
  Send, 
  Check, 
  RefreshCw, 
  Smartphone, 
  Upload, 
  ExternalLink
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import type { HevyStatus, TelegramStatus } from '../../../shared/types/integration';
import { cn } from '../../../shared/utils/cn';

export interface IntegrationsViewProps {
  isReadOnly?: boolean;
  planCapabilities?: {
    integrationsEnabled: boolean;
    telegramEnabled: boolean;
    importsEnabled: boolean;
  };
  hevy: {
    status: HevyStatus | null;
    key: string;
    setKey: (val: string) => void;
    onSave: () => void;
    onSync: () => void;
    onRemove: () => void;
    loading: boolean;
    syncing: boolean;
  };
  telegram: {
    status: TelegramStatus | null;
    code: { code: string; url: string } | null;
    onGenerate: () => void;
    onToggleNotify: (val: boolean) => void;
    loading: boolean;
    notifyOnWorkout: boolean;
  };
  imports: {
    onUpload: (file: File, type: 'mfp' | 'zepp') => void;
    importing: boolean;
  };
}

export function IntegrationsView({
  isReadOnly = false,
  planCapabilities,
  hevy,
  telegram,
  imports,
}: IntegrationsViewProps) {
  const { t } = useTranslation();
  const integrationsEnabled = planCapabilities?.integrationsEnabled ?? true;
  const telegramEnabled = planCapabilities?.telegramEnabled ?? true;
  const importsEnabled = planCapabilities?.importsEnabled ?? true;

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-12 pb-20")}>
      {isReadOnly && (
        <PremiumCard className="p-4 border-amber-500/20 bg-amber-500/5 text-amber-200 text-[10px] font-semibold uppercase tracking-[0.2em]">
          Demo Read-Only
        </PremiumCard>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* HEVY INTEGRATION */}
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-text-primary tracking-tight uppercase px-2">{t('settings.integrations.hevy.title')}</h2>
          <PremiumCard className="p-8 space-y-8 flex flex-col">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Dumbbell size={24} />
               </div>
               <div>
                  <h3 className="font-semibold text-text-primary text-lg">{t('settings.integrations.hevy.subtitle')}</h3>
                  {hevy.status?.enabled && (
                    <div className="flex items-center gap-1.5 mt-1">
                       <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                       <span className="text-[10px] font-semibold text-[color:var(--color-secondary)] uppercase tracking-[0.05em]">{t('settings.integrations.shared.connected')}</span>
                    </div>
                  )}
               </div>
            </div>

            {!hevy.status?.hasKey ? (
              <div className="space-y-4">
                {!integrationsEnabled && (
                  <p className="text-xs font-bold uppercase tracking-wider text-amber-300">
                    {t('settings.integrations.pro_only')}
                  </p>
                )}
                <div className="space-y-2">
                  <label className="text-[10px] font-semibold uppercase tracking-[0.05em] text-text-muted ml-1">API Key</label>
                  <input 
                    type="password"
                    placeholder={t('settings.integrations.hevy.hevy_placeholder')}
                    value={hevy.key}
                    disabled={isReadOnly || !integrationsEnabled}
                    onChange={(e) => { hevy.setKey(e.target.value); }}
                    className="form-field w-full rounded-2xl py-3.5 px-5"
                  />
                </div>
                <Button
                  type="button"
                  onClick={hevy.onSave}
                  disabled={isReadOnly || hevy.loading || !hevy.key || !integrationsEnabled}
                  className="w-full py-4 rounded-full bg-white text-black font-semibold hover:scale-105 active:scale-95 transition-all  shadow-white/10 disabled:opacity-50"
                >
                  {hevy.loading ? '...' : t('common.confirm')}
                </Button>
              </div>
            ) : (
              <div className="space-y-6 flex flex-col">
                <div className="bg-[color:var(--color-surface-container)] border border-[color:var(--color-outline-variant)] p-4 rounded-2xl flex items-center justify-between">
                   <div className="flex items-center gap-2 text-text-secondary text-sm font-medium">
                      <Check size={16} className="text-[color:var(--color-secondary)]" />
                      {t('settings.integrations.shared.active', { key: hevy.status.apiKeyMasked })}
                   </div>
                  <Button
                     type="button"
                     variant="ghost"
                     onClick={hevy.onRemove}
                     disabled={isReadOnly || hevy.loading || !integrationsEnabled}
                     className="h-auto p-0 text-[10px] font-semibold text-[color:var(--color-error)] uppercase tracking-[0.05em] hover:text-red-300 hover:bg-transparent transition-colors"
                   >
                     {t('settings.integrations.shared.remove')}
                   </Button>
                </div>

                <Button
                  type="button"
                  onClick={hevy.onSync}
                  disabled={isReadOnly || hevy.syncing || !integrationsEnabled}
                  className="w-full py-4 rounded-full bg-[color:var(--color-surface-container)] border border-[color:var(--color-outline-variant)] text-text-primary font-semibold hover:bg-white/10 transition-all flex items-center justify-center gap-3"
                >
                  <RefreshCw size={18} className={cn(hevy.syncing && "animate-spin")} />
                  {t('settings.integrations.hevy.sync_button')}
                </Button>
              </div>
            )}
          </PremiumCard>
        </div>

        {/* TELEGRAM INTEGRATION */}
        <div className="space-y-6">
          <h2 className="text-xl font-semibold text-text-primary tracking-tight uppercase px-2">{t('settings.integrations.telegram.title')}</h2>
          <PremiumCard className="p-8 space-y-8 flex flex-col">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                  <Send size={22} />
               </div>
               <div>
                  <h3 className="font-semibold text-text-primary text-lg">{t('settings.integrations.telegram.subtitle')}</h3>
                  {telegram.status?.linked && (
                    <div className="flex items-center gap-1.5 mt-1">
                       <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                       <span className="text-[10px] font-semibold text-[color:var(--color-secondary)] uppercase tracking-[0.05em]">{t('settings.integrations.shared.connected')}</span>
                    </div>
                  )}
               </div>
            </div>

            <div className="space-y-6 flex flex-col">
              {!telegramEnabled ? (
                <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-center">
                  <p className="text-xs font-bold uppercase tracking-wider text-amber-200">
                    {t('settings.integrations.pro_only')}
                  </p>
                </div>
              ) : telegram.status?.linked ? (
                <>
                  <div className="bg-[color:var(--color-surface-container)] border border-[color:var(--color-outline-variant)] p-6 rounded-3xl text-center">
                     <p className="text-sm font-bold text-text-primary mb-1">
                       {t('settings.integrations.telegram.connected', { username: telegram.status.telegram_username })}
                     </p>
                     <p className="text-xs text-text-muted">{t('settings.integrations.telegram.ready')}</p>
                  </div>

                  <div className="pt-6 border-t border-[color:var(--color-outline-variant)]">
                     <h4 className="text-xs font-semibold text-text-primary uppercase tracking-[0.05em] mb-4">{t('settings.integrations.telegram.notifications_title')}</h4>
                     <label 
                       className="flex items-start gap-4 p-4 rounded-2xl bg-[color:var(--color-surface-container)] border border-[color:var(--color-outline-variant)] hover:bg-white/[0.08] transition-all cursor-pointer group"
                     >
                  <input 
                          type="checkbox"
                          checked={telegram.notifyOnWorkout}
                          disabled={isReadOnly || !telegramEnabled}
                          onChange={(e) => { telegram.onToggleNotify(e.target.checked); }}
                          className="mt-1 w-4 h-4 rounded border-[color:var(--color-outline-variant)] bg-[color:var(--color-background)] text-[color:var(--color-primary)] focus:ring-indigo-500/20 cursor-pointer"
                        />
                        <div className="flex-1">
                           <p className="text-sm font-semibold text-text-primary group-hover:text-[color:var(--color-primary)] transition-colors">{t('settings.integrations.telegram.notifications_item_title')}</p>
                           <p className="text-xs text-text-muted mt-1 leading-relaxed">{t('settings.integrations.telegram.notifications_item_desc')}</p>
                        </div>
                     </label>
                  </div>
                </>
              ) : telegram.code ? (
                <div className="space-y-6 text-center flex flex-col justify-center">
                   <p className="text-sm font-medium text-text-secondary leading-relaxed">{t('settings.integrations.telegram.send_code')}</p>
                   <div className="text-4xl font-semibold text-text-primary tracking-[0.3em] bg-[color:var(--color-background)] py-6 px-4 rounded-3xl border border-[color:var(--color-outline-variant)] select-all shadow-inner tabular-nums my-4">
                      {telegram.code.code}
                   </div>
                   <a 
                     href={telegram.code.url}
                     target="_blank"
                     rel="noopener noreferrer"
                     className="inline-flex items-center gap-2 text-xs font-semibold text-[color:var(--color-primary)] uppercase tracking-[0.05em] hover:text-indigo-300 transition-colors"
                   >
                      {t('settings.integrations.telegram.open_bot')}
                      <ExternalLink size={14} />
                   </a>
                </div>
              ) : (
                <div className="flex flex-col justify-center">
                  <Button
                    type="button"
                    onClick={telegram.onGenerate}
                    disabled={isReadOnly || telegram.loading || !telegramEnabled}
                    className="w-full py-4 rounded-full bg-white text-black font-semibold hover:scale-105 active:scale-95 transition-all  shadow-white/10 disabled:opacity-50 flex items-center justify-center gap-3"
                  >
                    <Smartphone size={20} />
                    {t('settings.integrations.telegram.generate_code')}
                  </Button>
                </div>
              )}
            </div>
          </PremiumCard>
        </div>
      </div>

      {/* IMPORTS BENTO */}
      <div className="space-y-6 pt-12 border-t border-[color:var(--color-outline-variant)]">
         <h2 className="text-xl font-semibold text-text-primary tracking-tight uppercase px-2">{t('settings.integrations.imports.title')}</h2>
         {!importsEnabled && (
           <p className="px-2 text-xs font-bold uppercase tracking-wider text-amber-300">
             {t('settings.integrations.pro_only')}
           </p>
         )}
         <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <PremiumCard className="p-8 space-y-4 bg-gradient-to-br from-blue-900/20 to-transparent border-blue-500/20 group">
               <div className="flex items-center gap-3">
                  <div className="w-2 h-8 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                  <h3 className="font-semibold text-text-primary text-lg">MyFitnessPal</h3>
               </div>
               <p className="text-sm text-text-muted font-medium leading-relaxed">{t('settings.integrations.imports.mfp_desc')}</p>
               <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-[color:var(--color-outline-variant)] rounded-3xl hover:bg-[color:var(--color-surface-container)] hover:border-blue-500/30 cursor-pointer transition-all">
                  <Upload size={32} className="text-text-muted group-hover:text-blue-400 transition-colors mb-2" />
                  <span className="text-[10px] font-semibold uppercase tracking-[0.05em] text-text-muted">{t('settings.integrations.imports.click_to_select')}</span>
                  <input 
                    type="file" 
                    accept=".csv" 
                    className="hidden" 
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) imports.onUpload(file, 'mfp');
                    }}
                    disabled={imports.importing || !importsEnabled}
                  />
               </label>
            </PremiumCard>

            <PremiumCard className="p-8 space-y-4 bg-gradient-to-br from-orange-900/20 to-transparent border-[color:var(--color-tertiary)]/20 group">
               <div className="flex items-center gap-3">
                  <div className="w-2 h-8 rounded-full bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.5)]" />
                  <h3 className="font-semibold text-text-primary text-lg">Zepp Life</h3>
               </div>
               <p className="text-sm text-text-muted font-medium leading-relaxed">{t('settings.integrations.imports.zepp_desc')}</p>
               <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-[color:var(--color-outline-variant)] rounded-3xl hover:bg-[color:var(--color-surface-container)] hover:border-orange-500/30 cursor-pointer transition-all">
                  <Upload size={32} className="text-text-muted group-hover:text-[color:var(--color-tertiary)] transition-colors mb-2" />
                  <span className="text-[10px] font-semibold uppercase tracking-[0.05em] text-text-muted">{t('settings.integrations.imports.click_to_select')}</span>
                  <input 
                    type="file" 
                    accept=".csv" 
                    className="hidden" 
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) imports.onUpload(file, 'zepp');
                    }}
                    disabled={imports.importing || !importsEnabled}
                  />
               </label>
            </PremiumCard>
         </div>
      </div>

      {imports.importing && (
        <div className="fixed inset-0 bg-[#09090b]/80 backdrop-blur-md z-[100] flex items-center justify-center animate-in fade-in">
           <PremiumCard className="p-10 flex flex-col items-center gap-6 border-indigo-500/30 shadow-[0_0_50px_rgba(99,102,241,0.2)]">
              <RefreshCw size={48} className="text-[color:var(--color-primary)] animate-spin" />
              <div className="text-center space-y-2">
                 <h3 className="text-2xl font-semibold text-text-primary uppercase tracking-tight">{t('settings.integrations.imports.processing')}</h3>
                 <p className="text-sm text-text-muted font-medium">{t('settings.integrations.imports.waiting_desc', 'Processando seus dados, isso pode levar alguns instantes...')}</p>
              </div>
           </PremiumCard>
        </div>
      )}

    </div>
  );
}
