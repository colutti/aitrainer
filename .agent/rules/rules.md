---
trigger: always_on
---

## Metodologia

- **TDD obrigatório:** Primeiro escreva os testes (que devem falhar), depois implemente o mínimo para passar, depois refatore. Sem exceções.
- **Bug = Teste primeiro:** Quando um bug for reportado, crie um teste automatizado que reproduza o erro. Só então corrija o código e confirme que o teste passa.
- **Os testes são a fonte da verdade** do comportamento do sistema.
- **Adicione logs corretos: warnings, info, error, critical, etc. Use de forma sistema pra ajudar a identificar problemas

## Qualidade de Código

### Zero Tolerância
- **Zero** erros, warnings e hints em: Ruff, Pylint, Pyright, ESLint, TypeScript, builds de containers.
- Nunca desabilite regras de linting (`# noqa`, `// eslint-disable`, `# type: ignore`, `# pylint: disable`) a não ser que seja genuinamente necessário e documentado com justificativa no comentário.
- Prefira sempre corrigir o problema à raiz ao invés de silenciar o alerta.

### Python (Backend)
- Siga PEP 8, PEP 257 (docstrings), PEP 484 (type hints).
- Todo código Python deve ter type hints completos.
- Use os padrões do projeto: Repository Pattern, Service Layer, Dependency Injection.

### TypeScript (Frontend)
- Strict mode com `noUncheckedIndexedAccess`, `noUnusedLocals`, `noUnusedParameters`.
- ESLint com `strictTypeChecked` + `stylisticTypeChecked`.
- Testes de frontend devem mockear o backend em todos os casos, exceto se o usuário disser o contrário.

## Segurança

- **Tolerância zero para vulnerabilidades HIGH/CRITICAL** detectadas por Semgrep ou Trivy.
- `make security-check` deve ser executado antes de qualquer commit, junto com lint e testes.
- Nunca commite secrets, API keys, senhas ou tokens. O Trivy valida isso automaticamente.
- Sempre valide inputs do usuário e sanitize outputs.

## Containers & Infraestrutura

- O sistema usa **Podman**, não Docker.
- Sem erros ou warnings nos containers. Faça build dos containers para validar.
- Ferramentas de segurança (Semgrep, Trivy) rodam como containers efêmeros (`podman run --rm`), nunca dentro dos containers de produção.

## Documentação

- Toda documentação deve ser mantida **atualizada e fidedigna** ao estado real do código.
- Ao modificar funcionalidades, revise e atualize os documentos impactados: `README.md`, `GEMINI.md`, `CLAUDE.md`, docs de algoritmos, planos, etc.
- Só deve haver 1 `README.md` na raiz do projeto.
- Documentação mentirosa ou desatualizada é tratada como bug.

## Workflow Obrigatório

- Sempre que executar testes, execute o workflow `run-all-tests.md`. Mantenha esse arquivo atualizado.
- O workflow `run-all-tests.md` inclui: lint, type check, testes unitários, testes E2E e security scanning.
- Nenhuma tarefa é considerada concluída sem que TODO o workflow passe com zero erros.

## Limpeza & Organização

- Sempre apague arquivos temporários (logs, coverage, scripts de POC, screenshots).
- Arquivos temporários devem ficar em `tmp/` na raiz do projeto (que está no `.gitignore`).
- Nunca deixe arquivos desnecessários no repositório.
- Não reinvente a roda: prefira bibliotecas e padrões de mercado. Open source > pago, a não ser que se justifique.

## Testes

- Para testes locais via navegador ou quando precisar de um usuário, pergunte. Não assuma que exista nenhum usuário no sistema.
- Use `vi.spyOn(console, 'error').mockImplementation(() => {})` em testes que esperam erros de API.
- Use `fireEvent.submit(form)` ao invés de `fireEvent.click(submitButton)` para forms no JSDOM.