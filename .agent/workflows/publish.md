---
description: Workflow de como publicar os servicos em PROD
---

- Todos os servicos estao no servico Render (https://render.com/)
- Existe uma ferramenta de linha de comando chamada render pra comunicacao com o servico (https://render.com/docs/cli#non-interactive-mode). Consulte a documentacao de forma exaustiva pra entender como funciona a ferramenta.
- Se nao executou todos os testes desde a ultima mudanca, entao execute os segundo o arquivo test.md
- Faca uma analise se e necessario fazer alguma modificacao manual em producao.
- Se os testes passarem e nao e necessario ninhuma modificacao em prod, faca um commit e um publish do codigo. Manualmente eu vou ativar a publicao no Render.
- Se for necessaria alguma modificacao, informe ao usuario e peça uma aprovacao antes de continuar.
- Quando o usuario notificar que acabou o processo de publicacao, execute um smoke teste na url de prod.