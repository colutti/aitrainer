---
description: Workflow de como executar os testes
---

- Todos os servicos usados nessa solucao serao publicados usando o Docker Compose e seus Docker Files e deverao ser testados usandos os mesmos. Use Podman, nao Docker.
- Existem testes em backend e em frontend. Execute **todos** os testes encontrados.
- Certifique-se de que os containers do podman estao sendo executados corretamente
- Ao final dos testes automatizados, execute um smoke test usando o navegador. Use o mesmo usuario dos testes do cypress.
- So de a tarefa terminada quando nao houver nenhum erro relatado por testes manuais ou automatizados.
- Os testes nunca podem retornar warning. Se isso acontecer, corrija.