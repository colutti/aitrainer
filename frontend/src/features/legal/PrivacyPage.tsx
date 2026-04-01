import { Link } from 'react-router-dom';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 px-4 py-10">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-black tracking-tight mb-2">Politica de Privacidade</h1>
        <p className="text-sm text-zinc-400 mb-8">Ultima atualizacao: 2026-04-01</p>

        <div className="space-y-5 text-sm leading-7 text-zinc-200">
          <p>
            Esta politica explica como o FityQ coleta, usa e protege dados
            pessoais dos usuarios.
          </p>
          <p>
            Podemos coletar dados de cadastro, dados de uso da plataforma e dados
            fornecidos para personalizacao da experiencia.
          </p>
          <p>
            Usamos esses dados para autenticacao, seguranca, operacao do servico
            e melhoria do produto.
          </p>
          <p>
            Adotamos medidas tecnicas e organizacionais para reduzir risco de
            acesso nao autorizado.
          </p>
          <p>
            O FityQ utiliza criptografia ponta a ponta (E2EE) nos fluxos
            aplicaveis como parte das medidas de seguranca da informacao.
          </p>
          <p>
            O usuario pode solicitar revisao de dados pessoais conforme
            legislacao aplicavel e canais oficiais de suporte.
          </p>
        </div>

        <div className="mt-10">
          <Link to="/login" className="text-sm text-teal-300 hover:text-teal-200 transition-colors">
            Voltar para login
          </Link>
        </div>
      </div>
    </div>
  );
}
