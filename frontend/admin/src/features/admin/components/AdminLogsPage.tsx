import { Terminal, Cloud, FileText, AlertTriangle } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '../../../shared/components/ui/Button';
import { adminApi } from '../api/admin-api';

export function AdminLogsPage() {
  const [source, setSource] = useState<'local' | 'betterstack'>('local');
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchLogs() {
      setIsLoading(true);
      setError(null);
      try {
        if (source === 'local') {
          const res = await adminApi.getApplicationLogs(100);
          setLogs(res.logs);
        } else {
          // Verify betterstack return
          const res = await adminApi.getBetterStackLogs(100);
          // Assuming result.data matches Angular logic (array of objects with message)
           
          if (res && Array.isArray(res.data)) {
            setLogs(res.data.map((l) => {
              const item = l as { message?: string };
              return item.message ?? JSON.stringify(l);
            }));
          } else {
            setLogs([]);
          }
        }
      } catch {
        // console.error(err);
        setError('Erro ao carregar logs.');
        setLogs([]);
      } finally {
        setIsLoading(false);
      }
    }
    void fetchLogs();
  }, [source]);

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-700">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">Logs do Sistema</h1>
      </div>

      <div className="flex gap-2 md:gap-4 border-b border-border pb-4 overflow-x-auto">
        <Button
          variant={source === 'local' ? 'primary' : 'secondary'}
          onClick={() => { setSource('local'); }}
          className="gap-1 md:gap-2 text-xs md:text-sm shrink-0"
        >
          <FileText size={16} className="md:w-[18px] md:h-[18px]" />
          <span className="hidden sm:inline">Logs Locais</span>
          <span className="sm:hidden">Locais</span>
        </Button>
        <Button
          variant={source === 'betterstack' ? 'primary' : 'secondary'}
          onClick={() => { setSource('betterstack'); }}
          className="gap-1 md:gap-2 text-xs md:text-sm shrink-0"
        >
          <Cloud size={16} className="md:w-[18px] md:h-[18px]" />
          <span className="hidden sm:inline">BetterStack</span>
          <span className="sm:hidden">Stack</span>
        </Button>
      </div>

      <div className="flex-1 bg-black border border-border rounded-xl p-2 md:p-4 overflow-hidden flex flex-col font-mono text-xs shadow-inner">
        {error ? (
          <div className="flex items-center gap-2 text-red-400 p-4">
            <AlertTriangle size={18} />
            {error}
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center h-full text-text-muted animate-pulse gap-2">
            <Terminal size={24} />
            Carregando logs...
          </div>
        ) : logs.length === 0 ? (
           <div className="flex items-center justify-center h-full text-text-muted">
             Nenhum log encontrado.
           </div>
        ) : (
          <div className="overflow-y-auto h-full space-y-1 scrollbar-thin scrollbar-thumb-zinc-700 scrollbar-track-transparent pr-2">
            {logs.map((log, i) => (
              <div key={i} className="text-zinc-300 break-words hover:bg-white/5 px-2 py-0.5 rounded">
                <span className="text-zinc-500 select-none mr-2">{i+1}</span>
                {log}
              </div>
            ))}
            {/* Anchor to scroll to bottom could be added here */}
          </div>
        )}
      </div>
    </div>
  );
}
