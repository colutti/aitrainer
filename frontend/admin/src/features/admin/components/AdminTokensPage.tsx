import { RotateCw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

import { useNotificationStore } from '../../../../../src/shared/hooks/useNotification';
import type { TokenSummary, TokenTimeseries } from '../../../../../src/shared/types/admin';
import { adminApi } from '../api/admin-api';

export function AdminTokensPage() {
  const [tokenSummary, setTokenSummary] = useState<TokenSummary[]>([]);
  const [tokenTimeseries, setTokenTimeseries] = useState<TokenTimeseries[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [days, setDays] = useState(30);
  const [expandedUser, setExpandedUser] = useState<string | null>(null);

  const notify = useNotificationStore();

  const fetchTokenData = async (selectedDays: number) => {
    try {
      setIsLoading(true);
      const [summaryRes, timeseriesRes] = await Promise.all([
        adminApi.getTokenSummary(selectedDays),
        adminApi.getTokenTimeseries(selectedDays),
      ]);
      setTokenSummary(summaryRes.data);
      setTokenTimeseries(timeseriesRes.data);
    } catch {
      notify.error('Erro ao carregar dados de tokens');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTokenData(days).catch(console.error);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const handleDaysChange = (newDays: number) => {
    setDays(newDays);
    setExpandedUser(null);
  };

  // Calculate KPI metrics
  const totalTokensInput = tokenSummary.reduce((sum, item) => sum + item.total_input, 0);
  const totalTokensOutput = tokenSummary.reduce((sum, item) => sum + item.total_output, 0);
  const totalCost = tokenSummary.reduce((sum, item) => sum + (item.cost_usd ?? 0), 0);
  const avgTokensPerMessage =
    tokenSummary.length > 0
      ? Math.round(
          (tokenSummary.reduce((sum, item) => sum + item.total_input + item.total_output, 0) /
            tokenSummary.reduce((sum, item) => sum + item.message_count, 0)) *
            100,
        ) / 100
      : 0;

  return (
    <div className="space-y-6 h-full flex flex-col animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold text-text-primary">Token Analytics</h1>
          <button 
            onClick={() => { void fetchTokenData(days); }}
            disabled={isLoading}
            className="p-2 hover:bg-white/5 rounded-full transition-colors disabled:opacity-50"
            title="Atualizar"
            aria-label="Atualizar tokens"
          >
            <RotateCw size={20} className={`text-text-secondary ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Period Selector */}
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => {
                handleDaysChange(d);
              }}
              className={`px-3 md:px-4 py-2 rounded-lg font-medium text-sm md:text-base transition ${
                days === d
                  ? 'bg-accent text-white'
                  : 'bg-surface-secondary text-text-secondary hover:bg-surface-tertiary'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-text-secondary">Carregando dados...</div>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-surface-secondary rounded-lg p-4">
              <div className="text-text-secondary text-sm mb-2">Total Tokens (Input)</div>
              <div className="text-2xl font-bold text-text-primary">
                {(totalTokensInput / 1_000).toFixed(0)}K
              </div>
            </div>

            <div className="bg-surface-secondary rounded-lg p-4">
              <div className="text-text-secondary text-sm mb-2">Total Tokens (Output)</div>
              <div className="text-2xl font-bold text-text-primary">
                {(totalTokensOutput / 1_000).toFixed(0)}K
              </div>
            </div>

            <div className="bg-surface-secondary rounded-lg p-4">
              <div className="text-text-secondary text-sm mb-2">Custo Estimado (USD)</div>
              <div className="text-2xl font-bold text-text-primary">${totalCost.toFixed(2)}</div>
            </div>

            <div className="bg-surface-secondary rounded-lg p-4">
              <div className="text-text-secondary text-sm mb-2">Média Tokens/Msg</div>
              <div className="text-2xl font-bold text-text-primary">{avgTokensPerMessage}</div>
            </div>
          </div>

          {/* Chart */}
          <div className="bg-surface-secondary rounded-lg p-4">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Consumo de Tokens</h2>
            {tokenTimeseries.length > 0 ? (
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={tokenTimeseries} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                  <XAxis dataKey="date" stroke="#888" style={{ fontSize: '12px' }} />
                  <YAxis
                    stroke="#888"
                    width={70}
                    tickFormatter={(value) => `${(value / 1000).toFixed(1)}K`}
                    style={{ fontSize: '12px' }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1a1a1a',
                      border: '1px solid #444',
                      borderRadius: '8px',
                    }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="tokens_input"
                    stroke="#3b82f6"
                    name="Input Tokens"
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="tokens_output"
                    stroke="#10b981"
                    name="Output Tokens"
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center py-8 text-text-secondary">Sem dados disponíveis</div>
            )}
          </div>

          {/* Table */}
          <div className="bg-surface-secondary rounded-lg p-4 flex-1 overflow-auto">
            <h2 className="text-lg font-semibold text-text-primary mb-4">Por Usuário</h2>
            {tokenSummary.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-surface-tertiary">
                      <th className="text-left py-3 px-2 md:px-4 text-text-secondary font-medium">Email</th>
                      <th className="text-right py-3 px-2 md:px-4 text-text-secondary font-medium">
                        Tokens In
                      </th>
                      <th className="text-right py-3 px-2 md:px-4 text-text-secondary font-medium hidden md:table-cell">
                        Tokens Out
                      </th>
                      <th className="text-right py-3 px-2 md:px-4 text-text-secondary font-medium">
                        Custo
                      </th>
                      <th className="text-right py-3 px-2 md:px-4 text-text-secondary font-medium hidden lg:table-cell">
                        Msgs
                      </th>
                      <th className="text-right py-3 px-2 md:px-4 text-text-secondary font-medium hidden md:table-cell">
                        Última Ativ.
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {tokenSummary.map((item) => (
                      <tr
                        key={item._id}
                        className="border-b border-surface-tertiary hover:bg-surface-tertiary cursor-pointer transition"
                        onClick={() => {
                          setExpandedUser(expandedUser === item._id ? null : item._id);
                        }}
                      >
                        <td className="py-3 px-2 md:px-4 text-text-primary text-xs md:text-sm">{item._id}</td>
                        <td className="py-3 px-2 md:px-4 text-right text-text-primary text-xs md:text-sm">
                          {(item.total_input / 1_000).toFixed(0)}K
                        </td>
                        <td className="py-3 px-2 md:px-4 text-right text-text-primary hidden md:table-cell text-xs">
                          {(item.total_output / 1_000).toFixed(0)}K
                        </td>
                        <td className="py-3 px-2 md:px-4 text-right text-text-primary text-xs md:text-sm">
                          ${(item.cost_usd ?? 0).toFixed(2)}
                        </td>
                        <td className="py-3 px-2 md:px-4 text-right text-text-primary hidden lg:table-cell text-xs">
                          {item.message_count}
                        </td>
                        <td className="py-3 px-2 md:px-4 text-right text-text-secondary text-xs hidden md:table-cell">
                          {new Date(item.last_activity).toLocaleDateString('pt-BR')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-text-secondary">Sem dados disponíveis</div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
