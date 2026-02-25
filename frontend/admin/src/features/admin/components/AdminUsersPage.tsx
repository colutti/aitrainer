import { Search, Eye, Trash2, ArrowLeft, ArrowRight } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '../../../shared/components/ui/Button';
import { Input } from '../../../shared/components/ui/Input';
import { useConfirmation } from '../../../shared/hooks/useConfirmation';
import { useNotificationStore } from '../../../shared/hooks/useNotification';
import type { AdminUser } from '../../../shared/types/admin';
import { adminApi } from '../api/admin-api';

export function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);

  const { confirm } = useConfirmation();
  const notify = useNotificationStore();

  const fetchUsers = async (p = page, s = search) => {
    try {
      setIsLoading(true);
      const res = await adminApi.listUsers(p, 20, s);
      setUsers(res.users);
      setTotalPages(res.total_pages);
      setPage(res.page);
    } catch {
       // console.error(error);
      notify.error('Erro ao carregar usuários.');
    } finally {
      setIsLoading(false);
    }
  };

  // Debounced search effect
  useEffect(() => {
    const timer = setTimeout(() => {
      setPage(1); // Reset to page 1 on search
      void fetchUsers(1, search);
    }, 500);
    return () => { clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  // Page change effect (only if not triggered by search)
  // Actually, better to just call fetchUsers when page changes
  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
       setPage(newPage);
       void fetchUsers(newPage, search);
    }
  };

  const handleDelete = async (user: AdminUser) => {
    if (user.is_admin) {
      notify.error('Não é possível deletar usuários administradores.');
      return;
    }

    const isConfirmed = await confirm({
      title: 'Deletar Usuário',
      message: `Deseja realmente deletar o usuário ${user.email}? Esta ação removerá permanentemente todos os seus dados e memórias.`,
      confirmText: 'Deletar',
      type: 'danger',
    });

    if (isConfirmed) {
      try {
        await adminApi.deleteUser(user.email);
        notify.success('Usuário deletado com sucesso');
        void fetchUsers();
      } catch {
        // console.error(error)
        notify.error('Erro ao deletar usuário');
      }
    }
  };

  const handleView = async (user: AdminUser) => {
    try {
      notify.info(`Buscando detalhes de ${user.email}...`);
      const details = await adminApi.getUser(user.email);
      setSelectedUser(details);
    } catch {
      // console.error(error);
      notify.error('Erro ao buscar detalhes do usuário');
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-700">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">Gestão de Usuários</h1>
      </div>

      {/* Search */}
      <div>
        <Input
          placeholder="Buscar por email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); }}
          leftIcon={<Search size={18} />}
          className="max-w-md"
        />
      </div>

      {/* Table */}
      <div className="bg-dark-card border border-border rounded-xl overflow-hidden flex-1 flex flex-col">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-zinc-900 text-sm text-text-secondary uppercase tracking-wider">
              <tr>
                <th className="p-2 md:p-4 font-medium">Email</th>
                <th className="p-2 md:p-4 font-medium hidden md:table-cell">Nome</th>
                <th className="p-2 md:p-4 font-medium hidden lg:table-cell">Role</th>
                <th className="p-2 md:p-4 font-medium hidden lg:table-cell">Data Criação</th>
                <th className="p-2 md:p-4 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading && users.length === 0 ? (
                <tr>
                   <td colSpan={5} className="p-2 md:p-8 text-center text-text-muted">Carregando...</td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-2 md:p-8 text-center text-text-muted">Nenhum usuário encontrado.</td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.email} className="hover:bg-white/5 transition-colors group">
                    <td className="p-2 md:p-4 text-text-primary font-medium text-sm md:text-base">{user.email}</td>
                    <td className="p-2 md:p-4 text-text-secondary hidden md:table-cell text-sm">{user.display_name ?? user.email.split('@')[0] ?? '-'}</td>
                    <td className="p-2 md:p-4 hidden lg:table-cell">
                      <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                        user.is_admin
                          ? 'bg-yellow-500/20 text-yellow-500'
                          : 'bg-zinc-700 text-zinc-300'
                      }`}>
                        {user.is_admin ? 'ADMIN' : 'USER'}
                      </span>
                    </td>
                     <td className="p-2 md:p-4 text-text-secondary text-sm hidden lg:table-cell">
                      {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="p-2 md:p-4 text-right">
                      <div className="flex justify-end gap-1 md:gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => { void handleView(user); }}
                          title="Ver detalhes"
                        >
                          <Eye size={18} className="text-blue-400" />
                        </Button>
                        {!user.is_admin && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => { void handleDelete(user); }}
                            title={`Deletar ${user.email}`}
                            aria-label={`Deletar ${user.email}`}
                          >
                            <Trash2 size={18} className="text-red-400" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-border p-1 md:p-4 bg-zinc-900/50 flex justify-center items-center gap-0.5 md:gap-2 mt-auto">
             <button
               disabled={page === 1 || isLoading}
               onClick={() => { handlePageChange(page - 1); }}
               className="p-1 md:p-2 disabled:opacity-50"
             >
               <ArrowLeft size={14} className="md:w-4 md:h-4" />
             </button>
             <span className="text-[10px] md:text-sm text-text-secondary flex-shrink-0 px-1 md:px-2">
               {page}/{totalPages}
             </span>
             <button
               disabled={page === totalPages || isLoading}
               onClick={() => { handlePageChange(page + 1); }}
               className="p-1 md:p-2 disabled:opacity-50"
             >
               <ArrowRight size={14} className="md:w-4 md:h-4" />
             </button>
          </div>
        )}
      </div>
      
      {/* Details Modal (Overlay) */}
      {selectedUser && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-200"
          onClick={() => { setSelectedUser(null); }}
        >
          <div
             className="bg-dark-card border border-border p-6 rounded-xl max-w-[calc(100vw-2rem)] md:max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl"
             onClick={(e) => { e.stopPropagation(); }}
          >
             <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-text-primary">Detalhes do Usuário</h2>
                <Button variant="ghost" size="sm" onClick={() => { setSelectedUser(null); }}>
                  Fechar
                </Button>
             </div>
             <pre className="bg-black/40 p-4 rounded-lg text-green-400 text-sm overflow-x-auto border border-white/5">
               {JSON.stringify(selectedUser, null, 2)}
             </pre>
          </div>
        </div>
      )}
    </div>
  );
}
