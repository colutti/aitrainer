---
description: Workflow de como publicar os servicos em PROD
---

# 🚀 Workflow de Publicação (Production Deploy)

Este workflow garante que o código verificado localmente seja publicado com segurança no Render.

## 0. Pré-requisitos
- [ ] **Ambiente**: Estar na branch `main`.
- [ ] **Status**: Git status deve estar limpo (commite alterações pendentes).
- [ ] **CLI**: Comando `render` deve estar autenticado e funcional.

## 1. Validação Pré-Deploy (Crucial)
Antes de enviar qualquer código, valide se o build de produção passa localmente. (Evita erros de `tsconfig`, `environment.prod.ts` ou variáveis).

1. Execute a validação completa de testes (se não rodou recentemente):
   ```bash
   /test   # use o workflow de teste existente para rodar Backend e E2E
   ```
2. **Build de Produção Frontend** (Simulação):
   Obrigatório rodar para garantir que arquivos de teste (`.spec.ts`) não estão quebrando o bundle.
   ```bash
   cd frontend && npm run build
   # Se falhar, PARE. Corrija o erro antes de continuar.
   ```
3. Verificar integridade do Backend (Opcional):
   ```bash
   # Verifique se não há erros de sintaxe ou importação "perdidos"
   cd backend && python -m compileall src/
   ```

## 2. Preparação do Release
1. Identifique o Hash do Commit atual (será usado para rastreabilidade):
   ```bash
   COMMIT_HASH=$(git rev-parse HEAD)
   echo "Commit para deploy: $COMMIT_HASH"
   ```
2. Push para o repositório remoto:
   ```bash
   git push origin main
   ```

## 3. Execução do Deploy (Render CLI)
**IDs dos Serviços:**
- Backend: `srv-d5f2utqli9vc73dak390` (Manual)
- Frontend: `srv-d5f3e8u3jp1c73bkjbf0` (Automático no Push)

### Backend (Manual)
1. Disparar deploy manual atrelando ao commit específico:
   ```bash
   render deploys create srv-d5f2utqli9vc73dak390 --commit $COMMIT_HASH --confirm
   ```
   *Nota: Se possível use `--wait`. Caso contrário, monitore com `render deploys list`.*

### Frontend (Automático - Monitoramento)
1. Monitorar o status do deploy automático disparado pelo push:
   ```bash
   render deploys list srv-d5f3e8u3jp1c73bkjbf0 --output json
   ```
   *Verifique se o último deploy corresponde ao `$COMMIT_HASH` e se o status virou `live`.*

## 4. Verificação Pós-Deploy (Smoke Test)
Só considere sucesso se ambos retornarem sucesso.

1. **Backend Health**:
   ```bash
   curl -f -s https://aitrainer-backend.onrender.com/health || echo "❌ Backend falhou"
   ```
   *Esperado: `{"status":"healthy", ...}`*

2. **Frontend Availability**:
   ```bash
   curl -I -f -s https://aitrainer-frontend.onrender.com || echo "❌ Frontend falhou"
   ```
   *Esperado: `HTTP/2 200`*

## 5. Rollback (Em caso de falha)
Se o deploy falhar ou o smoke test quebrar:
1. Reverter o deploy no Render para a versão anterior via Dashboard ou CLI (`render deploys rollback <service_id>`).
2. Não fazer rollback no git (`git revert`) sem análise prévia.