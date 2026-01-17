---
description: 
---

# 🧪 Workflow de Testes

Este workflow consolida a execução de todas as suítes de teste do projeto para garantir a qualidade antes de qualquer publicação.

- Os testes dependem dos serviços (MongoDB, Qdrant, Mem0, API Backend) estarem rodando via Podman. Sempre garante que os containers estao sendo executados antes de fazer o teste.
- Sempre que for testar algo no navegador e nao encontrar o que esta buscando tente fazer um refresh do navegador.
- Certifique-se de que o backend está acessível e saudável.
- Execute testes unitários e de integração validando a cobertura de código.
- Todos os testes devem passar de toda a solucao.
- Warnings devem ser tratados e eliminados.
- Os testes do cypress devem rodar no container definido no Docker Compose. Monitore sua execucao e reporte.
- Os testes do cypress nao podem depender nem do backend nem dos bancos de dados. Mockear.
- Testes executar os testes do cypress sempre de pouco a pouco porque sao muitos testes e podem demorar demais resultando em timeout.
- Voce deve monitorar os logs dos containers.
- Se um teste falha, voce pode corrigir e reexecutar so ele ate estar corrigido, mas e necessario executar a suite de novo pq seu teste pode ter impactado em algo.
- Nao pode ter erros, warnings ou mensagens de deprecated que possam ser solucionadas por voce. Trate esses avisos como erros.
voce deve monitorar processos de build, containers, avisos de compilacao e pode usar ferramentas externas como black, etc.