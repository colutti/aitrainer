# Frontend Architecture Guidelines

Este documento descreve apenas padrões ainda visíveis no frontend atual.

## Estrutura de features

O frontend principal continua organizado por feature em `frontend/src/features`.

Padrão preferencial:

- `*Page.tsx`: coordena estado, hooks, navegação e integração com APIs
- `components/*View.tsx`: recebe props e concentra a renderização

Nem toda feature precisa seguir uma separação rígida, mas novas mudanças devem preservar responsabilidade clara entre orquestração e apresentação.

## Design system compartilhado

Os contratos visuais reutilizáveis vivem em:

- `frontend/src/shared/styles/ui-variants.ts`
- `frontend/src/shared/components/ui/premium/`

Peças centrais ainda em uso:

- `PREMIUM_UI`
- `PremiumCard`
- `ViewHeader`
- `FormField`

Ao expandir a UI:

- reutilize tokens e variantes existentes antes de criar estilos soltos
- mantenha consistência com as cores e superfícies já definidas
- use animações de forma contida e sem prejudicar legibilidade

## Testes

Unitários:

- ficam próximos da feature/componente
- usam Vitest e Testing Library
- devem validar comportamento observável, não implementação interna

E2E:

- vivem em `frontend/e2e/`
- usam fixtures e helpers de `frontend/e2e/helpers` e `frontend/e2e/fixtures`
- a validação oficial roda pelo fluxo containerizado do repositório

## Regras de manutenção

- `npm run lint` e `npm run typecheck` devem passar após qualquer edição em `frontend/`
- evite `any` quando um tipo local resolve o contrato
- mantenha textos sincronizados em `pt-BR`, `en-US` e `es-ES`
