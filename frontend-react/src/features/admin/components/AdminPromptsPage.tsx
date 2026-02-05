import { Eye, Search, ArrowLeft, ArrowRight, Copy } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import { adminApi, PromptLog } from '../api/admin-api';

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
  }, [searchEmail]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
      void fetchPrompts(newPage, searchEmail);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      notify.success('Copiado para a área de transferência!');
    } catch {
      notify.error('Erro ao copiar.');
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
            <thead className="bg-zinc-900 text-sm text-text-secondary uppercase tracking-wider">
              <tr>
                <th className="p-4 font-medium">Data</th>
                <th className="p-4 font-medium">Prompt Name</th>
                <th className="p-4 font-medium">User</th>
                <th className="p-4 font-medium">Model</th>
                <th className="p-4 font-medium">Tokens (In/Out)</th>
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading && prompts.length === 0 ? (
                 <tr><td colSpan={7} className="p-8 text-center text-text-muted">Carregando...</td></tr>
              ) : prompts.length === 0 ? (
                 <tr><td colSpan={7} className="p-8 text-center text-text-muted">Nenhum registro encontrado.</td></tr>
              ) : (
                prompts.map((log) => (
                  <tr key={log.id} className="hover:bg-white/5 transition-colors">
                    <td className="p-4 text-sm text-text-secondary whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="p-4 text-text-primary font-medium">{log.prompt_name || '-'}</td>
                    <td className="p-4 text-sm text-text-secondary">{log.user_email}</td>
                    <td className="p-4 text-sm font-mono text-blue-400">{log.model}</td>
                    <td className="p-4 text-sm text-text-secondary">
                        {log.tokens_input} / {log.tokens_output}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${
                          log.status === 'success' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                       <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => { setSelectedPrompt(log); }}
                          title="Ver detalhes"
                          aria-label="Ver detalhes"
                        >
                          <Eye size={18} className="text-text-primary" />
                        </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
            </table>
          </div>

          {totalPages > 1 && (
             <div className="border-t border-border p-4 bg-zinc-900/50 flex justify-center gap-2 mt-auto">
                <Button variant="ghost" disabled={page === 1} onClick={() => { handlePageChange(page - 1); }}>
                   <ArrowLeft size={16} />
                </Button>
                <span className="flex items-center px-4 text-sm text-text-secondary">
                   Página {page} de {totalPages}
                </span>
                <Button variant="ghost" disabled={page === totalPages} onClick={() => { handlePageChange(page + 1); }}>
                   <ArrowRight size={16} />
                </Button>
             </div>
          )}
       </div>

       {selectedPrompt && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-200"
          onClick={() => { setSelectedPrompt(null); }}
        >
          <div 
             className="bg-dark-card border border-border p-6 rounded-xl max-w-3xl w-full max-h-[85vh] overflow-hidden flex flex-col shadow-2xl"
             onClick={(e) => { e.stopPropagation(); }}
          >
             <div className="flex justify-between items-center mb-6 shrink-0">
                <h2 className="text-xl font-bold text-text-primary">Detalhes do Prompt</h2>
                <div className="flex gap-2">
                   <Button variant="secondary" size="sm" className="gap-2" onClick={() => { void copyToClipboard(JSON.stringify(selectedPrompt, null, 2)); }}>
                      <Copy size={16} /> Copiar JSON
                   </Button>
                   <Button variant="ghost" size="sm" onClick={() => { setSelectedPrompt(null); }}>
                      Fechar
                   </Button>
                </div>
             </div>
             
             <div className="flex-1 overflow-y-auto min-h-0 bg-black/40 rounded-lg border border-white/5 relative">
               <pre className="p-4 text-green-400 text-xs font-mono overflow-x-auto whitespace-pre-wrap">
                 {JSON.stringify(selectedPrompt, null, 2)}
               </pre>
             </div>
          </div>
        </div>
      )}
    </div>
  );
}
