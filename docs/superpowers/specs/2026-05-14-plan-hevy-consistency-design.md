# Plano Canônico e Consistência com Hevy

**Objetivo:** tornar o plano interno a única fonte de verdade do treino, com rotinas do Hevy ligadas e reconciliadas explicitamente quando divergirem.

## Regras centrais

- Cada usuário tem um único `UserPlan` ativo.
- O treino prescrito vive dentro do plano interno.
- Rotinas do Hevy são projeções linkadas desse treino.
- Quando houver vínculo, plano e Hevy devem permanecer equivalentes na estrutura prescrita.
- Diferenças de execução real, como carga usada e reps feitas no treino, não contam como inconsistência estrutural.
- Mudanças estruturais detectadas no Hevy exigem reconciliação explícita com o usuário.

## Inconsistência estrutural

Abre pendência quando houver diferença em qualquer item prescrito:

- exercício adicionado, removido ou trocado
- ordem dos exercícios
- sets prescritos
- faixa alvo de reps
- descanso
- notas/instruções materiais
- vínculo de rotina ou exercício perdido/incerto

Não abre pendência por si só para:

- carga executada
- reps realizadas no log
- PRs
- diferença apenas de nome quando o mapeamento do exercício for confiável

## Direção da arquitetura

- `UserPlan` continua sendo a fonte de verdade
- rotinas e exercícios passam a ter identidade estável no plano
- links com Hevy são explícitos e por ID, não por nome
- detecção de drift vira estado de domínio
- a IA deixa de escrever diretamente em estruturas críticas via payload genérico
- escrita estrutural passa a ser mediada por validação determinística

## Endurecimentos imediatos

1. impedir que updates parciais do `training_program` encolham rotinas ou agenda
2. impedir que updates do Hevy substituam toda a lista de exercícios por engano
3. garantir leitura completa das rotinas do Hevy antes de alegar revisão total
4. reduzir respostas do coach que extrapolam o que os tools realmente confirmaram

## Recuperação de prod

Escopo atual: somente `rafacolucci@gmail.com`.

- restaurar o plano interno com base híbrida entre Hevy atual e plano ideal confirmado
- relinkar as 5 rotinas `[AC]`
- mapear exercícios por identidade estável/template ID quando possível
- abrir pendências explícitas onde houver ambiguidade real
