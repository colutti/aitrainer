---
description: 
---

# 🧪 Workflow de Testes

Este workflow consolida a execução de todas as suítes de teste do projeto para garantir a qualidade antes de qualquer publicação.

## 1. Preparação do Ambiente
Os testes dependem dos serviços (MongoDB, Qdrant, Mem0, API Backend) estarem rodando via Podman.

### 1.1. Iniciar Serviços
```bash
# Na raiz do backend, use o Makefile
cd backend
make up
# Aguarde a inicialização (especialmente MongoDB e Qdrant)
sleep 15
```

### 1.2. Verificar Saúde
Certifique-se de que o backend está acessível e saudável.
```bash
curl -s http://localhost:8000/health | grep "healthy" || echo "⚠️ Backend/Serviços não estão saudáveis!"
```

## 2. Testes de Backend (Python)
Executa testes unitários e de integração validando a cobertura de código.

### 2.1. Execução (Pytest + Coverage)
```bash
cd backend
# Executa pytest com relatório de cobertura detalhado
.venv/bin/pytest --cov=src --cov-report=term-missing
```

**Critérios de Sucesso:**
- ✅ Todos os testes devem passar.
- 📊 Cobertura total deve ser > **90%**.
- ⚠️ Warnings devem ser tratados e eliminados.

## 3. Testes de Frontend (Angular)
Testes de componentes e serviços isolados.

### 3.1. Unit Tests (Jest)
```bash
cd frontend
npm test
```
*Nota: Se o comando travar em modo 'watch', certifique-se de usar `npm test -- --watch=false`.*

## 4. Testes End-to-End (Cypress)
Validação de fluxos completos de usuário. Requer Frontend e Backend rodando.

### 4.1. Execução Headless
```bash
cd frontend
npx cypress run
```

### 4.2. Diagnóstico de Falhas
- Verifique screenshots em `frontend/cypress/screenshots` se houver falhas.
- Verifique logs do backend para erros de API (500).

## 5. Smoke Test Local (Manual)
Após sucesso nos automatizados:
1. Abra o navegador com agente em `http://localhost:4200`.
2. Login com um dos usuarios dos testes do cypress.
3. Valide envio de mensagem e resposta do AI.

## 6. Encerramento
Após concluir, você pode parar os serviços se não for continuar desenvolvendo:
```bash
cd backend && make down
```