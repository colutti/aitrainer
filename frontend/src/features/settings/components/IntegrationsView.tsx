import { 
  Dumbbell, 
  Send, 
  Check, 
  RefreshCw, 
  Smartphone, 
  Copy, 
  Link2, 
  Upload, 
  ExternalLink
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { Button } from '../../../shared/components/ui/Button';
import { PremiumCard } from '../../../shared/components/ui/premium/PremiumCard';
import { PREMIUM_UI } from '../../../shared/styles/ui-variants';
import type { HevyStatus, HevyWebhookConfig, HevyWebhookCredentials, TelegramStatus } from '../../../shared/types/integration';
import { cn } from '../../../shared/utils/cn';

export interface IntegrationsViewProps {
  isReadOnly?: boolean;
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
  webhook: {
    config: HevyWebhookConfig | null;
    credentials: HevyWebhookCredentials | null;
    onGenerate: () => void;
    onRevoke: () => void;
    onCopy: (text: string) => void;
    loading: boolean;
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
  hevy,
  webhook,
  telegram,
  imports,
}: IntegrationsViewProps) {
  const { t } = useTranslation();

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "space-y-12 pb-20")}>
      {isReadOnly && (
        <PremiumCard className="p-4 border-amber-500/20 bg-amber-500/5 text-amber-200 text-[10px] font-black uppercase tracking-[0.2em]">
          Demo Read-Only
        </PremiumCard>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* HEVY INTEGRATION */}
        <div className="space-y-6">
          <h2 className="text-xl font-black text-white tracking-tight uppercase px-2">{t('settings.integrations.hevy.title')}</h2>
          <PremiumCard className="p-8 space-y-8 flex flex-col">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                  <Dumbbell size={24} />
               </div>
               <div>
                  <h3 className="font-black text-white text-lg">{t('settings.integrations.hevy.subtitle')}</h3>
                  {hevy.status?.enabled && (
                    <div className="flex items-center gap-1.5 mt-1">
                       <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                       <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">{t('settings.integrations.shared.connected')}</span>
                    </div>
                  )}
               </div>
            </div>

            {!hevy.status?.hasKey ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">API Key</label>
                  <input 
                    type="password"
                    placeholder={t('settings.integrations.hevy.hevy_placeholder')}
                    value={hevy.key}
                    disabled={isReadOnly}
                    onChange={(e) => { hevy.setKey(e.target.value); }}
                    className="form-field w-full rounded-2xl py-3.5 px-5"
                  />
                </div>
                <Button
                  type="button"
                  onClick={hevy.onSave}
                  disabled={isReadOnly || hevy.loading || !hevy.key}
                  className="w-full py-4 rounded-full bg-white text-black font-black hover:scale-105 active:scale-95 transition-all shadow-xl shadow-white/10 disabled:opacity-50"
                >
                  {hevy.loading ? '...' : t('common.confirm')}
                </Button>
              </div>
            ) : (
              <div className="space-y-6 flex flex-col">
                <div className="bg-white/5 border border-white/5 p-4 rounded-2xl flex items-center justify-between">
                   <div className="flex items-center gap-2 text-zinc-400 text-sm font-medium">
                      <Check size={16} className="text-emerald-400" />
                      {t('settings.integrations.shared.active', { key: hevy.status.apiKeyMasked })}
                   </div>
                  <Button
                     type="button"
                     variant="ghost"
                     onClick={hevy.onRemove}
                     disabled={isReadOnly || hevy.loading}
                     className="h-auto p-0 text-[10px] font-black text-red-400 uppercase tracking-widest hover:text-red-300 hover:bg-transparent transition-colors"
                   >
                     {t('settings.integrations.shared.remove')}
                   </Button>
                </div>

                <Button
                  type="button"
                  onClick={hevy.onSync}
                  disabled={isReadOnly || hevy.syncing}
                  className="w-full py-4 rounded-full bg-white/5 border border-white/10 text-white font-black hover:bg-white/10 transition-all flex items-center justify-center gap-3"
                >
                  <RefreshCw size={18} className={cn(hevy.syncing && "animate-spin")} />
                  {t('settings.integrations.hevy.sync_button')}
                </Button>

                <div className="pt-6 border-t border-white/5 mt-auto">
                   <h4 className="text-xs font-black text-white uppercase tracking-widest flex items-center gap-2 mb-4">
                      <Link2 size={14} /> {t('settings.integrations.hevy.webhook_title')}
                   </h4>
                   
                   {!webhook.config?.hasWebhook ? (
                     <Button
                       type="button"
                       onClick={webhook.onGenerate}
                       disabled={isReadOnly || webhook.loading}
                       className="w-full py-3 rounded-2xl bg-white/5 border border-dashed border-white/10 text-xs font-bold text-zinc-500 hover:border-indigo-500/50 hover:text-indigo-400 transition-all"
                     >
                       {t('settings.integrations.hevy.webhook_setup')}
                     </Button>
                   ) : (
                     <div className="space-y-3">
                        <div className="bg-black/20 p-3 rounded-xl border border-white/5 group relative">
                           <p className="text-[9px] text-zinc-600 font-black uppercase mb-1">{t('settings.integrations.hevy.webhook_url')}</p>
                           <div className="flex items-center justify-between gap-4">
                              <code className="text-[10px] text-indigo-300 truncate font-mono">{webhook.config.webhookUrl}</code>
                              <Button type="button" variant="ghost" size="icon" onClick={() => { webhook.onCopy(webhook.config?.webhookUrl ?? ''); }} className="h-6 w-6 text-zinc-500 hover:text-white hover:bg-transparent">
                                 <Copy size={14} />
                              </Button>
                           </div>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={webhook.onRevoke}
                          disabled={isReadOnly || webhook.loading}
                          className="w-full h-auto p-0 text-center text-[10px] font-black text-red-500/50 uppercase tracking-widest hover:text-red-400 hover:bg-transparent transition-colors"
                        >
                          {t('settings.integrations.hevy.webhook_revoke')}
                        </Button>
                     </div>
                   )}
                </div>
              </div>
            )}
          </PremiumCard>
        </div>

        {/* TELEGRAM INTEGRATION */}
        <div className="space-y-6">
          <h2 className="text-xl font-black text-white tracking-tight uppercase px-2">{t('settings.integrations.telegram.title')}</h2>
          <PremiumCard className="p-8 space-y-8 flex flex-col">
            <div className="flex items-center gap-4">
               <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                  <Send size={22} />
               </div>
               <div>
                  <h3 className="font-black text-white text-lg">{t('settings.integrations.telegram.subtitle')}</h3>
                  {telegram.status?.linked && (
                    <div className="flex items-center gap-1.5 mt-1">
                       <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                       <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">{t('settings.integrations.shared.connected')}</span>
                    </div>
                  )}
               </div>
            </div>

            <div className="space-y-6 flex flex-col">
              {telegram.status?.linked ? (
                <>
                  <div className="bg-white/5 border border-white/5 p-6 rounded-3xl text-center">
                     <p className="text-sm font-bold text-white mb-1">
                       {t('settings.integrations.telegram.connected', { username: telegram.status.telegram_username })}
                     </p>
                     <p className="text-xs text-zinc-500">{t('settings.integrations.telegram.ready')}</p>
                  </div>

                  <div className="pt-6 border-t border-white/5">
                     <h4 className="text-xs font-black text-white uppercase tracking-widest mb-4">{t('settings.integrations.telegram.notifications_title')}</h4>
                     <label 
                       className="flex items-start gap-4 p-4 rounded-2xl bg-white/5 border border-white/5 hover:bg-white/[0.08] transition-all cursor-pointer group"
                     >
                  <input 
                          type="checkbox"
                          checked={telegram.notifyOnWorkout}
                          disabled={isReadOnly}
                          onChange={(e) => { telegram.onToggleNotify(e.target.checked); }}
                          className="mt-1 w-4 h-4 rounded border-white/10 bg-black/40 text-indigo-500 focus:ring-indigo-500/20 cursor-pointer"
                        />
                        <div className="flex-1">
                           <p className="text-sm font-black text-white group-hover:text-indigo-400 transition-colors">{t('settings.integrations.telegram.notifications_item_title')}</p>
                           <p className="text-xs text-zinc-500 mt-1 leading-relaxed">{t('settings.integrations.telegram.notifications_item_desc')}</p>
                        </div>
                     </label>
                  </div>
                </>
              ) : telegram.code ? (
                <div className="space-y-6 text-center flex flex-col justify-center">
                   <p className="text-sm font-medium text-zinc-400 leading-relaxed">{t('settings.integrations.telegram.send_code')}</p>
                   <div className="text-4xl font-black text-white tracking-[0.3em] bg-black/40 py-6 px-4 rounded-3xl border border-white/10 select-all shadow-inner tabular-nums my-4">
                      {telegram.code.code}
                   </div>
                   <a 
                     href={telegram.code.url}
                     target="_blank"
                     rel="noopener noreferrer"
                     className="inline-flex items-center gap-2 text-xs font-black text-indigo-400 uppercase tracking-widest hover:text-indigo-300 transition-colors"
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
                    disabled={isReadOnly || telegram.loading}
                    className="w-full py-4 rounded-full bg-white text-black font-black hover:scale-105 active:scale-95 transition-all shadow-xl shadow-white/10 disabled:opacity-50 flex items-center justify-center gap-3"
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
      <div className="space-y-6 pt-12 border-t border-white/5">
         <h2 className="text-xl font-black text-white tracking-tight uppercase px-2">{t('settings.integrations.imports.title')}</h2>
         <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <PremiumCard className="p-8 space-y-4 bg-gradient-to-br from-blue-900/20 to-transparent border-blue-500/20 group">
               <div className="flex items-center gap-3">
                  <div className="w-2 h-8 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                  <h3 className="font-black text-white text-lg">MyFitnessPal</h3>
               </div>
               <p className="text-sm text-zinc-500 font-medium leading-relaxed">{t('settings.integrations.imports.mfp_desc')}</p>
               <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/5 rounded-3xl hover:bg-white/5 hover:border-blue-500/30 cursor-pointer transition-all">
                  <Upload size={32} className="text-zinc-600 group-hover:text-blue-400 transition-colors mb-2" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">{t('settings.integrations.imports.click_to_select')}</span>
                  <input 
                    type="file" 
                    accept=".csv" 
                    className="hidden" 
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) imports.onUpload(file, 'mfp');
                    }}
                    disabled={imports.importing}
                  />
               </label>
            </PremiumCard>

            <PremiumCard className="p-8 space-y-4 bg-gradient-to-br from-orange-900/20 to-transparent border-orange-500/20 group">
               <div className="flex items-center gap-3">
                  <div className="w-2 h-8 rounded-full bg-orange-500 shadow-[0_0_10px_rgba(249,115,22,0.5)]" />
                  <h3 className="font-black text-white text-lg">Zepp Life</h3>
               </div>
               <p className="text-sm text-zinc-500 font-medium leading-relaxed">{t('settings.integrations.imports.zepp_desc')}</p>
               <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-white/5 rounded-3xl hover:bg-white/5 hover:border-orange-500/30 cursor-pointer transition-all">
                  <Upload size={32} className="text-zinc-600 group-hover:text-orange-400 transition-colors mb-2" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-zinc-500">{t('settings.integrations.imports.click_to_select')}</span>
                  <input 
                    type="file" 
                    accept=".csv" 
                    className="hidden" 
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) imports.onUpload(file, 'zepp');
                    }}
                    disabled={imports.importing}
                  />
               </label>
            </PremiumCard>
         </div>
      </div>

      {imports.importing && (
        <div className="fixed inset-0 bg-[#09090b]/80 backdrop-blur-md z-[100] flex items-center justify-center animate-in fade-in">
           <PremiumCard className="p-10 flex flex-col items-center gap-6 border-indigo-500/30 shadow-[0_0_50px_rgba(99,102,241,0.2)]">
              <RefreshCw size={48} className="text-indigo-400 animate-spin" />
              <div className="text-center space-y-2">
                 <h3 className="text-2xl font-black text-white uppercase tracking-tight">{t('settings.integrations.imports.processing')}</h3>
                 <p className="text-sm text-zinc-500 font-medium">{t('settings.integrations.imports.waiting_desc', 'Processando seus dados, isso pode levar alguns instantes...')}</p>
              </div>
           </PremiumCard>
        </div>
      )}

    </div>
  );
}
