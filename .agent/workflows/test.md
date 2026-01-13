---
description: 
---

# 🧪 Workflow de Testes

Este workflow consolida a execução de todas as suítes de teste do projeto para garantir a qualidade antes de qualquer publicação.

- Os testes dependem dos serviços (MongoDB, Qdrant, Mem0, API Backend) estarem rodando via Podman.
- Sempre que for testar algo no navegador e nao encontrar o que esta buscando tente fazer um refresh do navegador.
- Certifique-se de que o backend está acessível e saudável.
- Execute testes unitários e de integração validando a cobertura de código.
- Todos os testes devem passar de toda a solucao.
- Warnings devem ser tratados e eliminados.
- Os testes do cypress devem rodar no container definido no Docker Compose. Monitore sua execucao e reporte.
- Os testes do cypress nao podem depender nem do backend nem dos bancos de dados. Mockear.
- A solucao devera ser testada em Chrome e Firefox usando cypress.