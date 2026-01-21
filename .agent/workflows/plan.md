---
description: 
---

Instrucoes para criar um plano

- Divida o plano em fases, cada uma com 1 entregavel testavel se possivel.
- Investigar quais testes tem que criados para ter uma boa cobertura para a nova funcionalidade
- Investivar o impacto da funcionalidade em testes existentes, etc. 
- Validar o impacto que isso pode ter na aplicacao.
- Entender e analisar a solucao para ter um melhor entendimento
- Testar a funcionalidade bem como regressao de problemas usando o workflow test.md
- Evitar testes via navegador, se algo puder ser testado que seja testado com um teste automatizado sempre que possivel.
- A aplicacao e publicada no render com docker. Veja o workflow publish.md
- So faca a publicacao em prod com o consentimento do usuario.
- Tem que haver testes para as funcionalidades criadas.
- Crie POCS para validar se o plano e possivel, sempre que possivel.
- Seja detalhado, sempre tente incluir diagramas, mockups, exemplos, antes e depois quando possivel.
- Se tiver duvidas, pergunte nao assuma.
- Se for usar bilbiotecas externas, escolha sempre a mais usada que seja opensource. leia a documentacao da ferramenta pra enteder seu codigo e como usar os metodos que voce pretende usar.
- Nao assuma que o codigo vai funcionar, teste.
- Revise o plano ao terminar em busca de lacunas.
