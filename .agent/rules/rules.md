---
trigger: always_on
---

## General

- Os testes do frontend devem mockear o backend em todos os casos, exceto se o usuario disser ao contrario.
- 0 tolerancia a warnings e hints, tanto do backend quanto do frontend e tambem dos containers. 
- TDD: Primeiro implemente os testes depois a funcionalidade.
- Quando um bug for reportado, crie um teste automatizado que simule o erro primeiro. Depois corrija o codigo e volte a executar o teste pra confirmar sucesso.
- Para testes locais via navegador ou quando precisar de um usuario pergunte por ele. Nao assuma que exista nenhum usuario no sistema.
- O sistema usa Podman, nao use Docker

## A tarefa so pode ser considerada terminada se:

- Sem erros de linting, seja pylint, eslint, ts lint. etc.
- Nao existem testes para funcionalidade.
- Existem erros ou warnings nos containers.