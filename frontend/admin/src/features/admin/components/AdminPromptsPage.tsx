import { Eye, Search, ArrowLeft, ArrowRight } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { PromptLog } from '../../../shared/types/admin';
import { adminApi } from '../api/admin-api';

import { PromptDetailModal } from './PromptDetailModal';

export function AdminPromptsPage() {
  const [prompts, setPrompts] = useState<PromptLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchEmail, setSearchEmail] = useState('');
  
  const [selectedPrompt, setSelectedPrompt] = useState<PromptLog | null>(null);
  
  const notify = useNotificationStore();

  const fetchPrompts = async (p = page, email = searchEmail) => {
    setLoading(true);
    try {
      const res = await adminApi.listPrompts(p, 20, email);
      setPrompts(res.prompts);
      setTotalPages(res.total_pages);
      setPage(res.page);
    } catch {
      notify.error('Erro ao carregar prompts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1);
      void fetchPrompts(1, searchEmail);
    }, 500);
    return () => { clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchEmail]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
      void fetchPrompts(newPage, searchEmail);
    }
  };


  const handleViewDetails = async (log: PromptLog) => {
    try {
      notify.info('Buscando detalhes do prompt...');
      const fullPrompt = await adminApi.getPrompt(log.id);
      setSelectedPrompt(fullPrompt);
    } catch {
      notify.error('Erro ao buscar detalhes do prompt');
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-700">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">Logs de Prompts</h1>
      </div>

      <div>
        <Input
          placeholder="Filtrar por email do usuário..."
          value={searchEmail}
          onChange={(e) => { setSearchEmail(e.target.value); }}
          leftIcon={<Search size={18} />}
          className="max-w-md"
        />
      </div>

       <div className="bg-dark-card border border-border rounded-xl overflow-hidden flex-1 flex flex-col">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
            <thead className="bg-zinc-900 text-xs md:text-sm text-text-secondary uppercase tracking-wider">
              <tr>
                <th className="p-2 md:p-4 font-medium">Data/Hora</th>
                <th className="p-2 md:p-4 font-medium">Tipo</th>
                <th className="p-2 md:p-4 font-medium hidden md:table-cell">User</th>
                <th className="p-2 md:p-4 font-medium hidden lg:table-cell">Model</th>
                <th className="p-2 md:p-4 font-medium hidden lg:table-cell">Tokens</th>
                <th className="p-2 md:p-4 font-medium hidden lg:table-cell">Duração</th>
                <th className="p-2 md:p-4 font-medium">Status</th>
                <th className="p-2 md:p-4 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading && prompts.length === 0 ? (
                 <tr><td colSpan={8} className="p-2 md:p-8 text-center text-text-muted">Carregando...</td></tr>
              ) : prompts.length === 0 ? (
                 <tr><td colSpan={8} className="p-2 md:p-8 text-center text-text-muted">Nenhum registro encontrado.</td></tr>
              ) : (
                prompts.map((log) => {
                  const date = new Date(log.timestamp);
                  const durationSec = (log.duration_ms / 1000).toFixed(2);
                  const promptType = log.prompt?.prompt_name ?? (log.prompt?.type === 'with_tools' ? 'chat' : 'resumo');

                  return (
                    <tr key={log.id} className="hover:bg-white/5 transition-colors">
                      <td className="p-2 md:p-4 text-xs md:text-sm text-text-secondary whitespace-nowrap">
                        {date.toLocaleString('pt-BR')}
                      </td>
                      <td className="p-2 md:p-4 text-xs md:text-sm">
                        <span className={`px-2 py-1 rounded font-mono text-[10px] md:text-xs font-bold ${
                          promptType === 'chat'
                            ? 'bg-blue-500/10 text-blue-400'
                            : 'bg-purple-500/10 text-purple-400'
                        }`}>
                          {promptType}
                        </span>
                      </td>
                      <td className="p-2 md:p-4 text-xs text-text-secondary hidden md:table-cell">{log.user_email}</td>
                      <td className="p-2 md:p-4 text-xs font-mono text-blue-400 hidden lg:table-cell">{log.model}</td>
                      <td className="p-2 md:p-4 text-xs text-text-secondary hidden lg:table-cell">
                          {log.tokens_input} / {log.tokens_output}
                      </td>
                      <td className="p-2 md:p-4 text-xs text-text-secondary hidden lg:table-cell">
                          {durationSec}s
                      </td>
                      <td className="p-2 md:p-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] md:text-xs font-bold uppercase ${
                            log.status === 'success' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
                        }`}>
                          {log.status === 'success' ? '✓' : '✗'}
                        </span>
                      </td>
                      <td className="p-2 md:p-4 text-right">
                         <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => { void handleViewDetails(log); }}
                            title="Ver detalhes"
                            aria-label="Ver detalhes"
                          >
                            <Eye size={16} className="text-text-primary" />
                          </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
            </table>
          </div>

          {totalPages > 1 && (
             <div className="border-t border-border p-1 md:p-4 bg-zinc-900/50 flex justify-center items-center gap-0.5 md:gap-2 mt-auto">
                <button disabled={page === 1} onClick={() => { handlePageChange(page - 1); }} className="p-1 md:p-2 disabled:opacity-50">
                   <ArrowLeft size={14} className="md:w-4 md:h-4" />
                </button>
                <span className="text-[10px] md:text-sm text-text-secondary flex-shrink-0 px-1 md:px-2">
                   {page}/{totalPages}
                </span>
                <button disabled={page === totalPages} onClick={() => { handlePageChange(page + 1); }} className="p-1 md:p-2 disabled:opacity-50">
                   <ArrowRight size={14} className="md:w-4 md:h-4" />
                </button>
             </div>
          )}
       </div>

      <PromptDetailModal
        selectedPrompt={selectedPrompt}
        onClose={() => { setSelectedPrompt(null); }}
      />
    </div>
  );
}
