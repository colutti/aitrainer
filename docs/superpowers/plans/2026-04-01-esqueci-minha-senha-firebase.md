# Esqueci Minha Senha (Firebase) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir recuperação de senha para usuários de login com e-mail/senha reutilizando exclusivamente o fluxo nativo do Firebase Auth, sem criar endpoint novo no backend.

**Architecture:** O fluxo fica 100% no frontend principal (`frontend/`): o usuário informa o e-mail na tela de login e o app chama `sendPasswordResetEmail(auth, email)`. A UI sempre mostra feedback genérico de sucesso para evitar enumeração de contas. O backend existente permanece inalterado.

**Tech Stack:** React 19, TypeScript, Zustand, Firebase Auth SDK, React Hook Form + Zod, Vitest + Testing Library.

---

## Abordagens Avaliadas

1. **Recomendada: Modal/ação de reset no LoginPage + Firebase SDK direto**
- Prós: menor esforço, sem backend, menor risco de regressão.
- Contras: lógica de reset fica no componente/auth hook.

2. **Rota dedicada `/forgot-password` + Firebase SDK direto**
- Prós: URL compartilhável e UX mais clara para fluxo dedicado.
- Contras: maior escopo (rota, navegação, testes adicionais) para benefício limitado agora.

3. **Backend intermediando reset**
- Prós: centraliza integração no servidor.
- Contras: desnecessário para Firebase reset; aumenta superfície de segurança e manutenção.

## Escopo e Requisitos

- Apenas app principal (`frontend/src/features/auth`).
- Apenas usuários com login e senha (não social).
- Reaproveitar serviço do provedor (Firebase) sem persistência/endpoint novo.
- Mensagens de UI não podem confirmar se o e-mail existe.
- Respeitar i18n (`pt-BR`, `en-US`, `es-ES`).

### Task 1: Cobrir comportamento esperado com testes (TDD)

**Files:**
- Modify: `frontend/src/features/auth/LoginPage.test.tsx`
- Modify: `frontend/src/shared/hooks/useAuth.test.ts` (se reset for exposto no store)

- [ ] **Step 1: Escrever teste falhando para clique em “Esqueci a senha”**
```tsx
it('should request password reset and show generic success feedback', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter><LoginPage /></MemoryRouter>);

  await user.type(screen.getByTestId('login-email'), 'person@example.com');
  await user.click(screen.getByRole('button', { name: /esqueci a senha/i }));

  await waitFor(() => {
    expect(sendPasswordResetEmail).toHaveBeenCalled();
    expect(screen.getByText(/se o e-mail estiver cadastrado/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Escrever teste falhando para e-mail inválido/vazio**
```tsx
it('should validate email before requesting reset', async () => {
  const user = userEvent.setup();
  render(<MemoryRouter><LoginPage /></MemoryRouter>);

  await user.click(screen.getByRole('button', { name: /esqueci a senha/i }));

  expect(sendPasswordResetEmail).not.toHaveBeenCalled();
  expect(screen.getByText(/e-mail inválido/i)).toBeInTheDocument();
});
```

- [ ] **Step 3: Rodar testes para confirmar falha inicial**
Run: `cd frontend && npm test -- LoginPage.test.tsx`
Expected: FAIL nos novos cenários de reset.

- [ ] **Step 4: Commit do ciclo vermelho**
```bash
git add frontend/src/features/auth/LoginPage.test.tsx frontend/src/shared/hooks/useAuth.test.ts
git commit -m "test(auth): add failing forgot-password scenarios"
```

### Task 2: Implementar reset usando Firebase (sem backend)

**Files:**
- Modify: `frontend/src/shared/hooks/useAuth.ts`
- Modify: `frontend/src/features/auth/LoginPage.tsx`

- [ ] **Step 1: Adicionar action `requestPasswordReset(email)` no auth store**
```ts
requestPasswordReset: async (email: string) => {
  const normalizedEmail = email.trim().toLowerCase();
  const { auth } = await import('../../features/auth/firebase');
  const { sendPasswordResetEmail } = await import('firebase/auth');
  await sendPasswordResetEmail(auth, normalizedEmail);
},
```

- [ ] **Step 2: Ligar botão “Esqueci a senha” ao fluxo de reset**
```tsx
const requestPasswordReset = useAuthStore((state) => state.requestPasswordReset);

const handleForgotPassword = async () => {
  const email = getValues('email');
  if (!email) {
    setError('auth.forgot_password_requires_email');
    return;
  }

  await requestPasswordReset(email);
  setError('auth.forgot_password_sent_generic');
};
```

- [ ] **Step 3: Tratar erro sem expor existência de conta**
```tsx
try {
  await requestPasswordReset(email);
} catch {
  // Mensagem genérica igual ao sucesso para evitar enumeração
}
setInfo(t('auth.forgot_password_sent_generic'));
```

- [ ] **Step 4: Rodar testes do arquivo alterado**
Run: `cd frontend && npm test -- LoginPage.test.tsx useAuth.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit do ciclo verde**
```bash
git add frontend/src/shared/hooks/useAuth.ts frontend/src/features/auth/LoginPage.tsx frontend/src/features/auth/LoginPage.test.tsx frontend/src/shared/hooks/useAuth.test.ts
git commit -m "feat(auth): add firebase forgot password flow"
```

### Task 3: i18n e mensagens de UX

**Files:**
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`

- [ ] **Step 1: Adicionar chaves de tradução**
```json
"auth": {
  "forgot_password": "Esqueci a senha",
  "forgot_password_requires_email": "Informe seu e-mail para recuperar a senha.",
  "forgot_password_sent_generic": "Se o e-mail estiver cadastrado, enviaremos um link para redefinir sua senha."
}
```

- [ ] **Step 2: Substituir texto hardcoded no botão/feedback**
Run: aplicar `t('auth.forgot_password')` no botão e `t(...)` nas mensagens.
Expected: tela sem strings hardcoded de reset.

- [ ] **Step 3: Rodar sanity de tradução**
Run: `cd frontend && npm test -- src/shared/utils/translation-integrity.test.ts`
Expected: PASS.

- [ ] **Step 4: Commit i18n**
```bash
git add frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json frontend/src/features/auth/LoginPage.tsx
git commit -m "chore(i18n): add forgot-password translations"
```

### Task 4: Validação final obrigatória do frontend

**Files:**
- Verify only

- [ ] **Step 1: Rodar lint**
Run: `cd frontend && npm run lint`
Expected: PASS sem warnings nos arquivos tocados.

- [ ] **Step 2: Rodar typecheck**
Run: `cd frontend && npm run typecheck`
Expected: PASS.

- [ ] **Step 3: Rodar suíte de testes relacionada**
Run: `cd frontend && npm test -- LoginPage.test.tsx useAuth.test.ts`
Expected: PASS.

- [ ] **Step 4: Commit final de verificação (opcional, se houver ajustes)**
```bash
git add frontend/src/features/auth/LoginPage.tsx frontend/src/shared/hooks/useAuth.ts frontend/src/features/auth/LoginPage.test.tsx frontend/src/shared/hooks/useAuth.test.ts frontend/src/locales/*.json
git commit -m "test(auth): verify forgot-password flow end-to-end in frontend"
```

## Riscos e Mitigações

- Enumeração de conta por mensagem de erro: mitigar com mensagem única para sucesso/falha de envio.
- Fluxo demo (`demo@fityq.it`) não deve quebrar login existente: manter caminho de reset independente do caminho de login demo.
- Rate limit do provedor: tratar erro de forma genérica na UI e manter logs apenas no cliente para depuração local.

## Critérios de Pronto

- Botão “Esqueci a senha” funcional no login do app principal.
- Nenhum endpoint novo no backend.
- Mensagens traduzidas em `pt-BR`, `en-US`, `es-ES`.
- `npm run lint` e `npm run typecheck` no `frontend/` passando após mudanças.
- Testes unitários do fluxo de reset passando.
