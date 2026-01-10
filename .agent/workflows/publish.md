---
description: Workflow de como publicar os servicos em PROD
---

- Todos os servicos estao no servico Render (https://render.com/)
- Existe uma ferramenta de linha de comando chamada render pra comunicacao com o servico (https://render.com/docs/cli#non-interactive-mode). Consulte a documentacao de forma exaustiva pra entender como funciona a ferramenta.
- Se nao executou todos os testes desde a ultima mudanca, entao execute os segundo o arquivo test.md
- Faca uma analise se e necessario fazer alguma modificacao manual em producao.
- Se os testes passarem e nao e necessario ninhuma modificacao em prod, faca um commit e um publish do codigo e manualmente faca o deploy no Render usando a ferramenta cli. O render esta configurado para nao fazer deploy automatico do git.
- Se for necessaria alguma modificacao, informe ao usuario e peça uma aprovacao antes de continuar.
- Espere o deploy terminar. Voce pode obter o estado do deploy usando a ferrament cli. 
- Quando o deploy terminar, execute um smoke teste na url de prod.
- Existem variaveis de ambiente definidas para DEV e PROD