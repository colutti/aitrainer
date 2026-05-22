# Plan V2 Hevy Sync

## Objective

Garantir que rotinas do plano vinculadas ao Hevy sejam sincronizadas antes de qualquer alteracao de treino entrar em vigor.

## Contract

- `TrainingRoutine.external_bindings[]`
  - `provider`
  - `external_routine_id`
  - `external_routine_name`
  - `last_synced_at`
  - `last_sync_error`
- `TrainingExercise.external_exercise_template_id`

## Sync Rule

- O plano continua sendo a fonte da verdade.
- A sincronizacao com Hevy so e obrigatoria quando:
  - o usuario tem `hevy_enabled=true` e `hevy_api_key`;
  - a rotina antiga ou nova possui binding `provider="hevy"`.
- `create_plan_from_discovery` nao toca no Hevy.
- `update_plan_section(section="training")`:
  1. valida o novo treino;
  2. sincroniza rotinas vinculadas no Hevy;
  3. so salva o plano se a sincronizacao inteira funcionar.

## Failure Policy

- Se uma rotina vinculada for removida do plano, a alteracao falha.
- Se uma mudanca estrutural de exercicio nao tiver `external_exercise_template_id` e nao puder reaproveitar o ID atual do Hevy pela mesma ordem e mesmo nome, a alteracao falha.
- Se a API do Hevy falhar, a alteracao falha.
- Em qualquer falha acima:
  - `saved=false`
  - `external_sync_failed=true`
  - o plano ativo permanece inalterado

## Exercise Mapping

- Quando o exercicio do plano ja tiver `external_exercise_template_id`, esse ID e usado.
- Caso contrario, o sync tenta reaproveitar o `exercise_template_id` atual do Hevy quando o exercicio estiver na mesma posicao e com o mesmo nome normalizado.
- Em sync bem-sucedido, o plano e enriquecido com `external_exercise_template_id`.

## Covered Tests

- sync bem-sucedida de rotina vinculada com enriquecimento de `external_exercise_template_id`
- bloqueio quando rotina vinculada e removida
- tool `update_plan_section` retorna `external_sync_failed` e nao salva o plano
