# Design Doc: Integração de Segurança e Overhaul de Qualidade

**Data:** 2026-03-06
**Status:** Aprovado

## 1. Contexto & Problema
O projeto AI Personal Trainer carecia de uma camada de análise de segurança automatizada (SAST, SCA e Secret Scanning) e de regras de qualidade mais rigorosas no `rules.md` para garantir que o desenvolvimento (incluindo o código gerado por IAs) siga padrões de excelência, TDD e PEP 8.

## 2. Objetivos
- Integrar **Semgrep** para análise estática de código (SAST).
- Integrar **Trivy** para análise de dependências (SCA) e segredos (Secret Scanning).
- Estabelecer uma "Constituição" no `rules.md` com tolerância zero para erros/warnings.
- Garantir que a documentação seja tratada como parte integrante do código.

## 3. Arquitetura da Solução

### 3.1 Ferramentas de Segurança
As ferramentas serão executadas como **containers efêmeros** via Podman para garantir isolamento e portabilidade sem "sujar" as imagens de produção.

- **Semgrep:** Focado em vulnerabilidades lógicas no código fonte (Python/TS).
- **Trivy:** Focado em vulnerabilidades em bibliotecas de terceiros (npm/pip) e detecção de segredos commitados.

### 3.2 Quality Gates
O fluxo de qualidade será composto por:
1. **Pre-commit:** Checks rápidos (Ruff).
2. **Local Workflow (`run-all-tests.md`):** Execução completa de testes + segurança.
3. **CI (GitHub Actions):** Validação final obrigatória para merge.

### 3.3 Regras de Qualidade (Novo rules.md)
O novo conjunto de regras impõe:
- TDD obrigatório em todas as alterações.
- Type hints obrigatórios em Python.
- Zero warnings em linters e builds.
- Documentação mentirosa = Bug.

## 4. Estratégia de Implementação
1. Atualizar arquivo de regras (`rules.md`, `AGENTS.md`).
2. Implementar alvos no `Makefile`.
3. Criar arquivos de configuração (`.semgrepignore`, `.trivyignore`).
4. Atualizar workflows (`run-all-tests.md` e CI).
5. Triage inicial de vulnerabilidades existentes.

## 5. Riscos & Mitigações
- **Falsos Positivos:** Resolvidos via `.semgrepignore` e `.trivyignore` com justificativa.
- **Performance:** Semgrep e Trivy são rápidos; o impacto na CI será minimizado rodando em paralelo.
