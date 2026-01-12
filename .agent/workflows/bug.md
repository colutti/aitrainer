---
description: Diretivas de como solucionar um bug
---

- Sempre teste reproduzir o bug antes usando um teste de backend ou de frontend. Olhe os testes existentes para determinar onde criar o novo teste.
- O ideal e que todos os bugs sejam identificados por testes para evitar regressao.
- Se o bug nao foi reproduzivel via testes automatizados explique porque e pode usar o navegador
- Se for usar o navegador, use o usuario cypress_user@test.com. Voce pode mudar a senha dele usando um script que esta em backend/scripts
- Quando o bug for corrigido execute todos os testes pra comprovar. o workflow test.md tem mais detalhes