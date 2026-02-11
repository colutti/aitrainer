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
- Nao desative erros, hints ou warnings no codigo a nao ser que seja realmente necessario. De preferencia por corrigir o problema sempre.
- Sempre que voce executar testes, execute o workflow run-all-tests.md. Mantenha esse arquivo atualizado.
- Os testes sao a fonte da verdade do codigo.
- So deve haver 1 README na solucao inteira que devera estar na raiz do projeto e deve ser mantido atualizado.
- Sempre apague arquivos temporarios criados e mantenha o projeto limpo. Arquivos de logs, coverage, scripts criados para POC, etc.

## A tarefa so pode ser considerada terminada se:

- Sem erros de linting, seja pylint, eslint, ts lint. etc.
- Nao existem testes para funcionalidade.
- Existem erros ou warnings nos containers.