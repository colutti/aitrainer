# Diretrizes Arquiteturais: Deep Space Premium

Este documento define os padrões técnicos e visuais estabelecidos durante a refatoração do frontend. Siga estas regras para garantir que a aplicação continue fácil de manter e testar.

## 1. Padrão Container / Presenter

Todas as novas funcionalidades devem ser divididas em dois arquivos:

### Container (`FeaturePage.tsx`)
- **Responsabilidade**: Gerenciamento de estado, chamadas de API (serviços/hooks), lógica de negócio.
- **Pura Lógica**: Não deve conter estilos complexos ou layouts detalhados.
- **Exemplo**: `DashboardPage.tsx` coordena o fetch de dados e passa as props para a `View`.

### Presenter (`FeatureView.tsx`)
- **Responsabilidade**: Renderização visual, animações, feedback de UI.
- **Componente Puro**: Deve receber tudo via `props`. Não deve disparar `fetch` diretamente.
- **Testabilidade**: 100% dos testes unitários de UI devem focar no Presenter usando mocks de props.

## 2. Design System Premium

Utilize as variantes centralizadas em `src/shared/styles/ui-variants.ts` para garantir consistência.

- **Bento Grid**: Use o padrão de cards de tamanhos variados para organizar informações.
- **Glassmorphism**: Utilize o componente `<PremiumCard />` para qualquer container de informação.
- **Animações**: Use o `framer-motion` para entradas suaves (`initial={{ opacity: 0 }}`).
- **Tipografia**: Use as classes `PREMIUM_UI.text.heading` e `PREMIUM_UI.text.label`.

## 3. Estratégia de Testes

### Unitários (Vitest + MSW)
- Localizados na mesma pasta do componente.
- Devem atingir ~100% de cobertura nos Presenters.
- Use `screen.getByTestId` como seletor prioritário.

### E2E Reais (Playwright)
- Localizados em `e2e/real/`.
- Validam o **Backend Real**.
- Utilize o helper `ui.navigateTo` e `ui.waitForToast` para resiliência.
- O cleanup é automático via `afterEach` integrado nas fixtures.

## 4. Zero Tolerância
- **Lint**: Proibido commitar com `warnings` ou `errors`.
- **Types**: Use interfaces estritas. Evite `any`.
- **Zod**: Todos os inputs de formulário devem ser validados via Schema.

---
*Assinado: Arquitetura Gemini CLI - Março 2026*
