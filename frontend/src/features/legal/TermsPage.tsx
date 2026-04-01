import { Link } from 'react-router-dom';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 px-4 py-10">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-black tracking-tight mb-2">Termos de Uso</h1>
        <p className="text-sm text-zinc-400 mb-8">Ultima atualizacao: 2026-04-01</p>

        <div className="space-y-5 text-sm leading-7 text-zinc-200">
          <p>Ao acessar ou usar o FityQ, voce concorda com estes Termos de Uso.</p>
          <p>
            O FityQ oferece recursos digitais para apoio a treinos, habitos e
            acompanhamento pessoal de saude e performance.
          </p>
          <p>
            O usuario e responsavel por manter suas credenciais em sigilo e por
            usar a plataforma de forma licita.
          </p>
          <p>
            O tratamento de dados pessoais segue a Politica de Privacidade.
          </p>
          <p>
            O FityQ utiliza criptografia ponta a ponta (E2EE) nos fluxos
            aplicaveis para reforcar a confidencialidade dos dados.
          </p>
          <p>
            O FityQ nao substitui orientacao medica, nutricional ou profissional
            individualizada.
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
