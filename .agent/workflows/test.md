# 🧪 Workflow de Testes

Este workflow consolida a execução de todas as suítes de teste do projeto para garantir a qualidade antes de qualquer publicação.

- Os testes dependem dos serviços (MongoDB, Qdrant, Mem0, API Backend) estarem rodando via Podman. Sempre garante que os containers estao sendo executados antes de fazer o teste. Faca sempre um rebuild de todos os containers.
- Sempre que for testar algo no navegador e nao encontrar o que esta buscando tente fazer um refresh do navegador.
- Certifique-se de que o backend está acessível e saudável.
- Os testes do cypress devem rodar no container definido no Docker Compose. Monitore sua execucao e reporte.
- Testes executar os testes do cypress sempre de pouco a pouco porque sao muitos testes e podem demorar demais resultando em timeout.
- Voce deve monitorar os logs dos containers.
- Se um teste falha, voce pode corrigir e reexecutar so ele ate estar corrigido, mas e necessario executar a suite de novo pq seu teste pode ter impactado em algo.
- Voce deve monitorar processos de build, containers, avisos de compilacao e pode usar ferramentas externas como black, etc.
- Nunca publique nada em producao sem antes o consentimento do usuario ou que o usuario peca pra voce.
- No warnings, no hints, no deprecations, no errors
- Provice summary of results

## Todos os Testes

scope,command,description
backend_unit,cd backend && pytest tests/unit,Runs backend unit tests
backend_perf,cd backend && pytest tests/performance,Runs performance benchmarks
backend_all,cd backend && pytest,Runs all backend tests
frontend_unit,cd frontend && npm test,Runs frontend unit tests
frontend_e2e,cd frontend && npx cypress run,Runs frontend E2E tests
validate_backend,cd backend && pytest,Runs full backend suite
validate_frontend,cd frontend && npm test,Runs full frontend suite
