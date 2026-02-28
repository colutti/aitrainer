import { Search, Eye, Trash2, ArrowLeft, ArrowRight, RotateCw } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '../../../../../src/shared/components/ui/Button';
import { Input } from '../../../../../src/shared/components/ui/Input';
import { useConfirmation } from '../../../../../src/shared/hooks/useConfirmation';
import { useNotificationStore } from '../../../../../src/shared/hooks/useNotification';
import type { AdminUser } from '../../../../../src/shared/types/admin';
import { adminApi } from '../api/admin-api';

export function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<any | null>(null);
  const [editUser, setEditUser] = useState<any>(null);

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
      const details = await adminApi.getUser(user.email) as any;
      setSelectedUser(details);
      setEditUser({
        subscription_plan: details.profile?.subscription_plan || 'Free',
        custom_message_limit: details.profile?.custom_message_limit || null,
      });
    } catch {
      // console.error(error);
      notify.error('Erro ao buscar detalhes do usuário');
    }
  };

  const handleUpdate = async () => {
    if (!selectedUser?.profile?.email) return;
    try {
      setIsLoading(true);
      await adminApi.updateUser(selectedUser.profile.email, editUser);
      notify.success('Usuário atualizado com sucesso');
      void handleView({ email: selectedUser.profile.email } as AdminUser);
    } catch {
      notify.error('Erro ao atualizar usuário');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-700">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-text-primary">Gestão de Usuários</h1>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => { void fetchUsers(page, search); }}
          disabled={isLoading}
          title="Atualizar"
          aria-label="Atualizar usuários"
        >
          <RotateCw size={20} className={isLoading ? 'animate-spin' : ''} />
        </Button>
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
                <th className="p-2 md:p-4 font-medium hidden lg:table-cell">Plano / Msg</th>
                <th className="p-2 md:p-4 font-medium hidden lg:table-cell">Data Criação</th>
                <th className="p-2 md:p-4 font-medium text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading && users.length === 0 ? (
                <tr>
                   <td colSpan={6} className="p-2 md:p-8 text-center text-text-muted">Carregando...</td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-2 md:p-8 text-center text-text-muted">Nenhum usuário encontrado.</td>
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
                    <td className="p-2 md:p-4 hidden lg:table-cell text-sm text-text-secondary">
                      {(() => {
                        const plan = user.subscription_plan || 'Free';
                        const customLimit = user.custom_message_limit;
                        const isFree = plan === 'Free';
                        const planLimits: Record<string, number> = {
                          Free: 20,
                          Basic: 100,
                          Pro: 300,
                          Premium: 1000,
                        };
                        const baseLimit = planLimits[plan] ?? 20;
                        const limit = customLimit ?? baseLimit;
                        const used = isFree ? (user.total_messages_sent || 0) : (user.messages_sent_this_month || 0);
                        const usageColor = used >= limit ? 'text-red-400 font-bold' : 'text-text-secondary';
                        
                        return (
                          <div className="flex flex-col">
                            <span className="font-bold text-white mb-0.5">{plan}</span>
                            <span className={`text-[11px] uppercase tracking-wider ${usageColor}`}>
                              {used} / {limit} {customLimit ? '(Custom)' : ''}
                            </span>
                          </div>
                        );
                      })()}
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
             className="bg-dark-card border border-border p-4 md:p-6 rounded-xl max-w-[calc(100vw-2rem)] md:max-w-3xl lg:max-w-5xl w-full max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col lg:flex-row gap-6 mt-4 md:mt-0"
             onClick={(e) => { e.stopPropagation(); }}
          >
            <div className="flex-1 min-w-0">
              <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-text-primary">Estatísticas</h2>
              </div>
              <pre className="bg-black/40 p-4 rounded-lg text-green-400 text-xs sm:text-sm overflow-x-auto border border-white/5 whitespace-pre-wrap break-words">
                {JSON.stringify(selectedUser.stats, null, 2)}
              </pre>
              <h2 className="text-2xl font-bold text-text-primary mt-6 mb-4">Perfil</h2>
              <pre className="bg-black/40 p-4 rounded-lg text-green-400 text-xs sm:text-sm overflow-x-auto border border-white/5 whitespace-pre-wrap word-break-all">
                {JSON.stringify({ ...selectedUser.profile, photo_base64: '...base64...' }, null, 2)}
              </pre>
            </div>

            <div className="flex-1 min-w-0 bg-zinc-900/50 p-4 md:p-6 rounded-lg border border-border">
               <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold text-text-primary">Editar Assinatura</h2>
                  <Button variant="ghost" size="sm" onClick={() => { setSelectedUser(null); }}>
                    Fechar
                  </Button>
               </div>
               
               <div className="space-y-4">
                 <div>
                   <label className="block text-sm font-medium text-text-secondary mb-1">
                     Plano
                   </label>
                   <select 
                     className="w-full bg-dark-card border border-border rounded-lg p-2 text-text-primary"
                     value={editUser.subscription_plan}
                     onChange={(e) => setEditUser({ ...editUser, subscription_plan: e.target.value })}
                   >
                     <option value="Free">Free</option>
                     <option value="Basic">Basic</option>
                     <option value="Pro">Pro</option>
                     <option value="Premium">Premium</option>
                   </select>
                 </div>

                 <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                      Limite customizado de mensagens (Opcional - null remove o limite customizado)
                    </label>
                    <div className="flex gap-2 mb-2 flex-wrap">
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="bg-white/5 hover:bg-white/10 text-xs"
                        onClick={() => {
                          const base = editUser.subscription_plan === 'Premium' ? 1000 : editUser.subscription_plan === 'Pro' ? 300 : editUser.subscription_plan === 'Basic' ? 100 : 20;
                          const current = editUser.custom_message_limit ?? base;
                          setEditUser({ ...editUser, custom_message_limit: Math.max(0, current - 10) });
                        }}
                      >- 10 Msg</Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="bg-white/5 hover:bg-white/10 text-xs"
                        onClick={() => {
                          const base = editUser.subscription_plan === 'Premium' ? 1000 : editUser.subscription_plan === 'Pro' ? 300 : editUser.subscription_plan === 'Basic' ? 100 : 20;
                          const current = editUser.custom_message_limit ?? base;
                          setEditUser({ ...editUser, custom_message_limit: current + 10 });
                        }}
                      >+ 10 Msg</Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="bg-white/5 hover:bg-white/10 text-xs"
                        onClick={() => {
                          const base = editUser.subscription_plan === 'Premium' ? 1000 : editUser.subscription_plan === 'Pro' ? 300 : editUser.subscription_plan === 'Basic' ? 100 : 20;
                          const current = editUser.custom_message_limit ?? base;
                          setEditUser({ ...editUser, custom_message_limit: current + 100 });
                        }}
                      >+ 100 Msg</Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="bg-white/5 hover:bg-white/10 text-xs text-red-400"
                        onClick={() => {
                          setEditUser({ ...editUser, custom_message_limit: null });
                        }}
                      >Remover Limite (Padrão)</Button>
                    </div>
                    <Input 
                      type="number"
                      placeholder="Ex: 50"
                      value={editUser.custom_message_limit ?? ''}
                      onChange={(e) => setEditUser({ ...editUser, custom_message_limit: e.target.value ? parseInt(e.target.value) : null })}
                    />
                 </div>

                 <Button 
                    className="w-full mt-4" 
                    onClick={() => { void handleUpdate(); }}
                    disabled={isLoading}
                 >
                   Salvar Alterações
                 </Button>
               </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
