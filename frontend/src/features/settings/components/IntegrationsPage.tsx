import { Upload, Check, RefreshCw, Smartphone, Database, Send, Copy, Link2 } from 'lucide-react';
import { useState, useEffect } from 'react';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { HevyStatus, HevyWebhookConfig, HevyWebhookCredentials, ImportResult, TelegramStatus } from '../../../shared/types/integration';
import { integrationsApi } from '../api/integrations-api';

export function IntegrationsPage() {
  const notify = useNotificationStore();
  
  // Hevy State
  const [hevyStatus, setHevyStatus] = useState<HevyStatus | null>(null);
  const [hevyKey, setHevyKey] = useState('');
  const [hevyLoading, setHevyLoading] = useState(false);
  const [hevySyncing, setHevySyncing] = useState(false);
  const [webhookConfig, setWebhookConfig] = useState<HevyWebhookConfig | null>(null);
  const [webhookCredentials, setWebhookCredentials] = useState<HevyWebhookCredentials | null>(null);
  const [webhookLoading, setWebhookLoading] = useState(false);

  // Telegram State
  const [telegramStatus, setTelegramStatus] = useState<TelegramStatus | null>(null);
  const [telegramCode, setTelegramCode] = useState<{ code: string; url: string } | null>(null);
  const [telegramLoading, setTelegramLoading] = useState(false);
  const [telegramNotifyOnWorkout, setTelegramNotifyOnWorkout] = useState(true);
  const [telegramNotifyOnNutrition, setTelegramNotifyOnNutrition] = useState(false);
  const [telegramNotifyOnWeight, setTelegramNotifyOnWeight] = useState(false);

  // Import State
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    void loadHevyStatus();
    void loadTelegramStatus();
    void loadWebhookConfig();
  }, []);

  async function loadHevyStatus() {
    try {
      const status = await integrationsApi.getHevyStatus();
      setHevyStatus(status ?? null);
    } catch {
      // ignore
    }
  }

  async function loadTelegramStatus() {
    try {
      const status = await integrationsApi.getTelegramStatus();
      setTelegramStatus(status ?? null);
      if (status) {
        setTelegramNotifyOnWorkout(status.telegram_notify_on_workout ?? true);
        setTelegramNotifyOnNutrition(status.telegram_notify_on_nutrition ?? false);
        setTelegramNotifyOnWeight(status.telegram_notify_on_weight ?? false);
      }
    } catch {
      // ignore
    }
  }

  async function loadWebhookConfig() {
    try {
      const config = await integrationsApi.getWebhookConfig();
      setWebhookConfig(config ?? null);
    } catch {
      // ignore
    }
  }

  async function handleSaveHevy() {
    if (!hevyKey) return;
    setHevyLoading(true);
    try {
      const status = await integrationsApi.saveHevyKey(hevyKey);
      setHevyStatus(status ?? null);
      setHevyKey('');
      notify.success('Chave da Hevy salva com sucesso!');
    } catch {
      notify.error('Erro ao salvar chave da Hevy.');
    } finally {
      setHevyLoading(false);
    }
  }

  async function handleSyncHevy() {
    setHevySyncing(true);
    try {
      const res = await integrationsApi.syncHevy();
      if (res) {
        notify.success(`Sincronização concluída! Importados: ${String(res.imported)}, Ignorados: ${String(res.skipped)}`);
        await loadHevyStatus();
      }
    } catch {
      notify.error('Erro ao sincronizar Hevy.');
    } finally {
      setHevySyncing(false);
    }
  }

  async function handleRemoveHevy() {
    setHevyLoading(true);
    try {
      const status = await integrationsApi.removeHevyKey();
      setHevyStatus(status ?? null);
      notify.success('Integração Hevy removida com sucesso!');
    } catch {
      notify.error('Erro ao remover integração Hevy.');
    } finally {
      setHevyLoading(false);
    }
  }

  async function handleGenerateWebhook() {
    setWebhookLoading(true);
    try {
      const creds = await integrationsApi.generateWebhook();
      if (creds) {
        setWebhookCredentials(creds);
        await loadWebhookConfig();
        notify.success('Webhook gerado com sucesso!');
      }
    } catch {
      notify.error('Erro ao gerar webhook.');
    } finally {
      setWebhookLoading(false);
    }
  }

  async function handleRevokeWebhook() {
    setWebhookLoading(true);
    try {
      await integrationsApi.revokeWebhook();
      setWebhookConfig({ hasWebhook: false, webhookUrl: null, authHeader: null });
      setWebhookCredentials(null);
      notify.success('Webhook revogado com sucesso!');
    } catch {
      notify.error('Erro ao revogar webhook.');
    } finally {
      setWebhookLoading(false);
    }
  }

  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      notify.success('Copiado para a área de transferência!');
    } catch {
      notify.error('Erro ao copiar.');
    }
  }

  async function handleGenerateTelegram() {
    setTelegramLoading(true);
    try {
      const res = await integrationsApi.generateTelegramCode();
      setTelegramCode(res ?? null);
    } catch {
      notify.error('Erro ao gerar código do Telegram.');
    } finally {
      setTelegramLoading(false);
    }
  }

  async function handleTelegramNotificationChange(
    field: 'workout' | 'nutrition' | 'weight',
    value: boolean
  ) {
    try {
      await integrationsApi.updateUserNotifications({
        [`telegram_notify_on_${field}`]: value
      });

      // Update local state
      if (field === 'workout') setTelegramNotifyOnWorkout(value);
      if (field === 'nutrition') setTelegramNotifyOnNutrition(value);
      if (field === 'weight') setTelegramNotifyOnWeight(value);

      notify.success('Preferência de notificação atualizada!');
    } catch {
      notify.error('Erro ao atualizar preferência de notificação.');
    }
  }

  async function handleUpload(file: File, type: 'mfp' | 'zepp') {
    setImporting(true);
    try {
      let res: ImportResult;
      if (type === 'mfp') {
        res = await integrationsApi.uploadMfpCsv(file);
      } else {
        res = await integrationsApi.uploadZeppLifeCsv(file);
      }
      
      notify.success(`Importação concluída! Criados: ${String(res.created)}, Atualizados: ${String(res.updated)}`);
      if (res.errors > 0) {
        notify.info(`${String(res.errors)} erros encontrados durante a importação.`);
      }
    } catch (err) {
      console.error(err);
      notify.error('Erro ao importar arquivo.');
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* Hevy Integration */}
      <section className="bg-dark-card border border-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center gap-3 border-b border-border pb-4">
           <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-500">
             <DumbbellIcon />
           </div>
           <div>
             <h2 className="text-xl font-bold text-text-primary">Hevy</h2>
             <p className="text-sm text-text-secondary">Sincronização automática de treinos.</p>
           </div>
           {hevyStatus?.enabled && <BadgeConnected />}
        </div>

        <div className="space-y-4 pt-2">
           {!hevyStatus?.hasKey ? (
             <div className="flex gap-4 items-end">
               <div className="flex-1">
                 <Input 
                   id="hevy-key" 
                   label="API Key" 
                   placeholder="Cole sua chave API do Hevy aqui" 
                   value={hevyKey}
                   onChange={(e) => { setHevyKey(e.target.value); }}
                   type="password"
                 />
               </div>
               <Button onClick={() => void handleSaveHevy()} isLoading={hevyLoading} disabled={!hevyKey}>
                 Salvar
               </Button>
             </div>
           ) : (
             <div className="flex flex-col gap-4">
               <div className="bg-green-500/5 border border-green-500/20 p-4 rounded-xl flex items-center justify-between">
                 <div className="flex items-center gap-2 text-green-500 text-sm font-medium">
                   <Check size={16} />
                   Integração ativa. Chave: {hevyStatus.apiKeyMasked}
                 </div>
                 <Button variant="ghost" size="sm" onClick={() => void handleRemoveHevy()} isLoading={hevyLoading} className="text-red-400 hover:text-red-300">
                   Remover
                 </Button>
               </div>
               <Button 
                 variant="secondary" 
                 className="w-full gap-2" 
                 onClick={() => void handleSyncHevy()} 
                 isLoading={hevySyncing}
                >
                 <RefreshCw size={16} className={hevySyncing ? "animate-spin" : ""} />
                 Sincronizar Agora
               </Button>
               {hevyStatus.lastSync && (
                 <p className="text-xs text-center text-text-muted">Última sincronização: {new Date(hevyStatus.lastSync).toLocaleString()}</p>
               )}

               {/* Webhook Configuration */}
               <div className="border-t border-border pt-4 mt-4">
                 <h3 className="text-sm font-bold text-text-primary mb-3 flex items-center gap-2">
                   <Link2 size={16} />
                   Webhook para Sincronização Automática
                 </h3>
                 {!webhookConfig?.hasWebhook ? (
                   <Button
                     variant="secondary"
                     className="w-full gap-2"
                     onClick={() => void handleGenerateWebhook()}
                     isLoading={webhookLoading}
                   >
                     Configurar Webhook
                   </Button>
                 ) : (
                   <div className="space-y-3">
                     <div className="bg-zinc-900 p-3 rounded-lg">
                       <label className="text-xs text-text-secondary block mb-1">URL do Webhook</label>
                       <div className="flex items-center gap-2">
                         <code className="text-xs text-text-primary flex-1 truncate">{webhookConfig.webhookUrl}</code>
                         <Button
                           size="sm"
                           variant="ghost"
                           onClick={() => void copyToClipboard(webhookConfig.webhookUrl || '')}
                         >
                           <Copy size={14} />
                         </Button>
                       </div>
                     </div>
                     <div className="bg-zinc-900 p-3 rounded-lg">
                       <label className="text-xs text-text-secondary block mb-1">Auth Header</label>
                       <div className="flex items-center gap-2">
                         <code className="text-xs text-text-primary flex-1 truncate">{webhookConfig.authHeader}</code>
                         <Button
                           size="sm"
                           variant="ghost"
                           onClick={() => void copyToClipboard(webhookConfig.authHeader || '')}
                         >
                           <Copy size={14} />
                         </Button>
                       </div>
                     </div>
                     {webhookCredentials && (
                       <div className="bg-yellow-500/10 border border-yellow-500/20 p-3 rounded-lg">
                         <p className="text-xs text-yellow-600 font-medium mb-2">⚠️ Copie agora - não será mostrado novamente</p>
                         <code className="text-xs text-text-primary block break-all">{webhookCredentials.authHeader}</code>
                       </div>
                     )}
                     <Button
                       variant="ghost"
                       className="w-full text-red-400 hover:text-red-300"
                       onClick={() => void handleRevokeWebhook()}
                       isLoading={webhookLoading}
                     >
                       Revogar Webhook
                     </Button>
                   </div>
                 )}
               </div>
             </div>
           )}
        </div>
      </section>

      {/* Telegram Integration */}
      <section className="bg-dark-card border border-border rounded-2xl p-6 space-y-4">
        <div className="flex items-center gap-3 border-b border-border pb-4">
           <div className="w-10 h-10 bg-sky-500/10 rounded-xl flex items-center justify-center text-sky-500">
             <Send size={20} />
           </div>
           <div>
             <h2 className="text-xl font-bold text-text-primary">Telegram Bot</h2>
             <p className="text-sm text-text-secondary">Receba notificações e logs rápidos pelo chat.</p>
           </div>
           {telegramStatus?.linked && <BadgeConnected />}
        </div>

        <div className="pt-2 space-y-4">
          {telegramStatus?.linked ? (
             <>
               <div className="text-center p-4 bg-zinc-900 rounded-xl">
                 <p className="text-green-500 font-bold mb-1">Conectado como @{telegramStatus.telegram_username}</p>
                 <p className="text-sm text-text-secondary">O bot está pronto para enviar alertas.</p>
               </div>

               {/* Notification Preferences */}
               <div className="border-t border-border pt-4 space-y-3">
                 <h3 className="text-sm font-bold text-text-primary">Receber notificações por Telegram:</h3>

                 <div className="flex items-center gap-3 p-3 bg-zinc-900 rounded-lg hover:bg-zinc-800 cursor-pointer transition-colors" onClick={() => void handleTelegramNotificationChange('workout', !telegramNotifyOnWorkout)}>
                   <input
                     type="checkbox"
                     checked={telegramNotifyOnWorkout}
                     onChange={(e) => void handleTelegramNotificationChange('workout', e.target.checked)}
                     className="w-4 h-4 cursor-pointer"
                   />
                   <div className="flex-1">
                     <p className="text-sm font-medium text-text-primary">Análise de Treinos</p>
                     <p className="text-xs text-text-secondary">Quando sincronizar treinos da Hevy</p>
                   </div>
                 </div>

                 <div className="flex items-center gap-3 p-3 bg-zinc-900 rounded-lg hover:bg-zinc-800 cursor-pointer transition-colors" onClick={() => void handleTelegramNotificationChange('nutrition', !telegramNotifyOnNutrition)}>
                   <input
                     type="checkbox"
                     checked={telegramNotifyOnNutrition}
                     onChange={(e) => void handleTelegramNotificationChange('nutrition', e.target.checked)}
                     className="w-4 h-4 cursor-pointer"
                   />
                   <div className="flex-1">
                     <p className="text-sm font-medium text-text-primary">Nutrição</p>
                     <p className="text-xs text-text-secondary">Resumo diário de nutrição</p>
                   </div>
                 </div>

                 <div className="flex items-center gap-3 p-3 bg-zinc-900 rounded-lg hover:bg-zinc-800 cursor-pointer transition-colors" onClick={() => void handleTelegramNotificationChange('weight', !telegramNotifyOnWeight)}>
                   <input
                     type="checkbox"
                     checked={telegramNotifyOnWeight}
                     onChange={(e) => void handleTelegramNotificationChange('weight', e.target.checked)}
                     className="w-4 h-4 cursor-pointer"
                   />
                   <div className="flex-1">
                     <p className="text-sm font-medium text-text-primary">Peso</p>
                     <p className="text-xs text-text-secondary">Atualizações de peso corporal</p>
                   </div>
                 </div>
               </div>
             </>
          ) : telegramCode ? (
             <div className="text-center space-y-4">
               <p className="text-text-primary font-medium">Envie este código para o nosso bot:</p>
               <div className="text-3xl font-mono font-bold text-gradient-start tracking-widest bg-zinc-900 p-4 rounded-xl select-all">
                 {telegramCode.code}
               </div>
               <a 
                 href={telegramCode.url} 
                 target="_blank" 
                 rel="noopener noreferrer"
                 className="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 underline"
               >
                 Abrir Bot no Telegram
               </a>
             </div>
          ) : (
             <Button className="w-full gap-2" onClick={() => void handleGenerateTelegram()} isLoading={telegramLoading}>
                <Smartphone size={18} />
                Gerar Código de Conexão
             </Button>
          )}
        </div>
      </section>

      {/* Imports Section */}
      <section className="bg-dark-card border border-border rounded-2xl p-6 space-y-6">
         <div className="flex items-center gap-3 border-b border-border pb-4">
           <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center text-purple-500">
             <Database size={20} />
           </div>
           <div>
             <h2 className="text-xl font-bold text-text-primary">Importação de Dados</h2>
             <p className="text-sm text-text-secondary">Importe históricos de outros apps.</p>
           </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* MFP */}
          <div className="space-y-3">
             <h3 className="font-bold text-text-primary flex items-center gap-2">
               <span className="w-2 h-2 rounded-full bg-blue-500" />
               MyFitnessPal (CSV)
             </h3>
             <p className="text-xs text-text-muted">Importe seus logs de nutrição exportados do MFP.</p>
             <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-zinc-700 rounded-xl hover:bg-white/5 cursor-pointer transition-colors group">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-8 h-8 mb-2 text-zinc-500 group-hover:text-gradient-start transition-colors" />
                    <p className="text-xs text-text-secondary">Clique para selecionar CSV</p>
                </div>
                <input 
                  type="file" 
                  accept=".csv" 
                  className="hidden" 
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) void handleUpload(file, 'mfp');
                  }}
                  disabled={importing}
                />
             </label>
          </div>

          {/* Zepp Life */}
          <div className="space-y-3">
             <h3 className="font-bold text-text-primary flex items-center gap-2">
               <span className="w-2 h-2 rounded-full bg-orange-500" />
               Zepp Life (CSV)
             </h3>
             <p className="text-xs text-text-muted">Importe histórico de peso e composição corporal.</p>
             <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-zinc-700 rounded-xl hover:bg-white/5 cursor-pointer transition-colors group">
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <Upload className="w-8 h-8 mb-2 text-zinc-500 group-hover:text-gradient-start transition-colors" />
                    <p className="text-xs text-text-secondary">Clique para selecionar CSV</p>
                </div>
                <input 
                  type="file" 
                  accept=".csv" 
                  className="hidden" 
                  onChange={(e) => {
                     const file = e.target.files?.[0];
                     if(file) void handleUpload(file, 'zepp');
                  }}
                  disabled={importing}
                />
             </label>
          </div>
        </div>
        
        {importing && (
           <div className="flex items-center justify-center gap-2 text-sm text-gradient-start animate-pulse">
              <RefreshCw size={16} className="animate-spin" />
              Processando arquivo...
           </div>
        )}
      </section>

    </div>
  );
}

function DumbbellIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6.5 6.5 11 11"/><path d="m21 21-1-1"/><path d="m3 3 1 1"/><path d="m18 22 4-4"/><path d="m2 6 4-4"/><path d="m3 10 7-7"/><path d="m14 21 7-7"/></svg>
  );
}

function BadgeConnected() {
  return (
    <span className="ml-auto px-2 py-0.5 bg-green-500/10 text-green-500 text-[10px] font-bold uppercase rounded-full border border-green-500/20">
      Conectado
    </span>
  );
}
