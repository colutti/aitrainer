# Chat + Telegram Image Analysis (PRO/Premium) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir envio de fotos para análise por IA no chat do app e no Telegram, com acesso restrito a assinantes PRO/Premium e atualização de descrição dos planos na landing e em configurações.

**Architecture:** Reutilizar o fluxo atual de conversa e estender o contrato de mensagem para multimodal (texto + imagem). Centralizar a regra de permissão por plano no backend e reaproveitar a mesma regra no endpoint HTTP (`/message`) e no webhook Telegram. No frontend, adicionar upload com preview no chat e atualizar os textos de plano em i18n.

**Tech Stack:** FastAPI, Pydantic, LangChain/LangGraph, Telegram Bot API, React 19 + Zustand + Vitest, i18next JSON locales, Pytest.

---

## File Structure / Ownership

- Modify: `backend/src/core/subscription.py`
- Modify: `backend/src/api/models/message.py`
- Modify: `backend/src/api/endpoints/message.py`
- Modify: `backend/src/services/trainer.py`
- Modify: `backend/src/services/llm_client.py`
- Modify: `backend/src/services/telegram_service.py`
- Test: `backend/tests/test_subscription_plan_config.py`
- Test: `backend/tests/unit/api/test_message_endpoints.py`
- Test: `backend/tests/unit/services/test_trainer_streaming.py`
- Test: `backend/tests/unit/services/test_telegram_service.py`

- Modify: `frontend/src/shared/types/chat.ts`
- Modify: `frontend/src/shared/hooks/useChat.ts`
- Modify: `frontend/src/features/chat/components/ChatView.tsx`
- Test: `frontend/src/shared/hooks/useChat.test.ts`
- Test: `frontend/src/features/chat/components/ChatView.test.tsx`

- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`
- Test: `frontend/src/features/landing/components/Pricing.test.tsx`
- Test: `frontend/src/features/settings/components/SubscriptionPage.test.tsx`

---

### Task 1: Feature Gate de Imagem por Plano (Backend Core + API Contract)

**Files:**
- Modify: `backend/src/core/subscription.py`
- Modify: `backend/src/api/models/message.py`
- Test: `backend/tests/test_subscription_plan_config.py`
- Test: `backend/tests/unit/api/test_message_endpoints.py`

- [ ] **Step 1: Escrever teste falhando para permissão de imagem por plano**

```python
# backend/tests/test_subscription_plan_config.py
from src.core.subscription import can_use_image_input


def test_image_input_allowed_only_for_pro_and_premium():
    assert can_use_image_input("Pro") is True
    assert can_use_image_input("Premium") is True
    assert can_use_image_input("Free") is False
    assert can_use_image_input("Basic") is False
```

- [ ] **Step 2: Rodar teste e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/test_subscription_plan_config.py -k image_input -v`
Expected: FAIL com `ImportError`/`AttributeError` para `can_use_image_input`.

- [ ] **Step 3: Implementar helper mínimo de permissão**

```python
# backend/src/core/subscription.py
IMAGE_INPUT_ALLOWED_PLANS = {SubscriptionPlan.PRO, SubscriptionPlan.PREMIUM}


def can_use_image_input(subscription_plan: str | None) -> bool:
    try:
        return SubscriptionPlan(subscription_plan) in IMAGE_INPUT_ALLOWED_PLANS
    except (ValueError, TypeError):
        return False
```

- [ ] **Step 4: Estender request model para payload multimodal**

```python
# backend/src/api/models/message.py
class MessageRequest(BaseModel):
    user_message: str = Field(..., min_length=1, max_length=5000)
    image_base64: str | None = Field(default=None, max_length=8_000_000)
    image_mime_type: str | None = Field(default=None, pattern=r"^image/(jpeg|png|webp)$")
```

- [ ] **Step 5: Adicionar teste de endpoint negando imagem para Free/Basic**

```python
# backend/tests/unit/api/test_message_endpoints.py

def test_message_ai_rejects_image_for_basic_plan():
    # mock profile.subscription_plan = "Basic"
    # payload inclui image_base64 + image_mime_type
    # assert status_code == 403
    # assert response.json()["detail"] == "IMAGE_NOT_ALLOWED_FOR_PLAN"
```

- [ ] **Step 6: Passar validação no endpoint `/message`**

```python
# backend/src/api/endpoints/message.py
from src.core.subscription import can_use_image_input

if message.image_base64 and not can_use_image_input(profile.subscription_plan):
    raise HTTPException(status_code=403, detail="IMAGE_NOT_ALLOWED_FOR_PLAN")
```

- [ ] **Step 7: Rodar suíte de testes deste task**

Run: `cd backend && .venv/bin/pytest tests/test_subscription_plan_config.py tests/unit/api/test_message_endpoints.py -v`
Expected: PASS com cenários de gate por plano e contrato de request.

- [ ] **Step 8: Commit**

```bash
git add backend/src/core/subscription.py backend/src/api/models/message.py backend/src/api/endpoints/message.py backend/tests/test_subscription_plan_config.py backend/tests/unit/api/test_message_endpoints.py
git commit -m "feat: add image input entitlement for pro and premium plans"
```

---

### Task 2: Pipeline Multimodal no AITrainerBrain + LLMClient

**Files:**
- Modify: `backend/src/services/trainer.py`
- Modify: `backend/src/services/llm_client.py`
- Test: `backend/tests/unit/services/test_trainer_streaming.py`

- [ ] **Step 1: Escrever teste falhando para envio multimodal ao LLM client**

```python
# backend/tests/unit/services/test_trainer_streaming.py
@pytest.mark.asyncio
async def test_send_message_ai_passes_image_payload_to_llm(mock_deps):
    # arrange trainer + profile Pro
    # call send_message_ai(..., image_payload={...})
    # assert llm.stream_with_tools recebeu input_data["user_image"]
```

- [ ] **Step 2: Rodar teste e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/unit/services/test_trainer_streaming.py -k image_payload -v`
Expected: FAIL por assinatura atual de `send_message_ai` sem imagem.

- [ ] **Step 3: Estender assinatura do brain para imagem opcional**

```python
# backend/src/services/trainer.py
async def send_message_ai(
    self,
    user_email: str,
    user_input: str,
    background_tasks: Optional[BackgroundTasks] = None,
    is_telegram: bool = False,
    image_payload: dict | None = None,
):
    ...
    input_data = self.prompt_builder.build_input_data(...)
    input_data["user_image"] = image_payload
```

- [ ] **Step 4: Adaptar montagem de mensagens no LLM client para multimodal**

```python
# backend/src/services/llm_client.py
if input_data.get("user_image"):
    image = input_data["user_image"]
    user_msg = {
        "role": "user",
        "content": [
            {"type": "text", "text": input_data.get("user_message", "")},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{image['mime_type']};base64,{image['base64']}"},
            },
        ],
    }
    # injeta user_msg no payload final para providers compatíveis
```

- [ ] **Step 5: Garantir fallback explícito para provider sem suporte**

```python
# backend/src/services/llm_client.py
if input_data.get("user_image") and not self.supports_multimodal:
    raise ValueError("IMAGE_INPUT_NOT_SUPPORTED_BY_PROVIDER")
```

- [ ] **Step 6: Rodar testes do task**

Run: `cd backend && .venv/bin/pytest tests/unit/services/test_trainer_streaming.py -v`
Expected: PASS com cobertura de envio de imagem e fallback.

- [ ] **Step 7: Commit**

```bash
git add backend/src/services/trainer.py backend/src/services/llm_client.py backend/tests/unit/services/test_trainer_streaming.py
git commit -m "feat: add multimodal image payload to ai message pipeline"
```

---

### Task 3: Suporte a Foto no Telegram + Gate de Plano

**Files:**
- Modify: `backend/src/services/telegram_service.py`
- Test: `backend/tests/unit/services/test_telegram_service.py`

- [ ] **Step 1: Escrever teste falhando para foto no Telegram (usuário Premium)**

```python
# backend/tests/unit/services/test_telegram_service.py
@patch("src.services.telegram_service.Bot")
@patch("src.services.telegram_service.Update")
async def test_handle_message_photo_allowed_plan_calls_ai(...):
    # update.message.photo com lista de PhotoSize
    # repo retorna link com user_email
    # brain.get_user_profile retorna subscription_plan="Premium"
    # assert brain.send_message_sync(..., image_payload=...) chamado
```

- [ ] **Step 2: Escrever teste falhando para foto no Telegram (plano Basic)**

```python
async def test_handle_message_photo_disallowed_plan_returns_upgrade_message(...):
    # subscription_plan="Basic"
    # assert bot.send_message contém texto de upgrade
    # assert brain.send_message_sync não chamado
```

- [ ] **Step 3: Rodar testes e confirmar falha**

Run: `cd backend && .venv/bin/pytest tests/unit/services/test_telegram_service.py -k photo -v`
Expected: FAIL sem suporte a `update.message.photo`.

- [ ] **Step 4: Implementar extração e envio da foto**

```python
# backend/src/services/telegram_service.py
photo = update.message.photo[-1] if update.message and update.message.photo else None
if photo:
    tg_file = await self.bot.get_file(photo.file_id)
    image_bytes = await tg_file.download_as_bytearray()
    image_payload = {
        "base64": base64.b64encode(bytes(image_bytes)).decode("utf-8"),
        "mime_type": "image/jpeg",
    }
```

- [ ] **Step 5: Aplicar gate por assinatura no fluxo Telegram**

```python
profile = self.brain.get_user_profile(link.user_email)
if image_payload and not can_use_image_input(getattr(profile, "subscription_plan", None)):
    await self.bot.send_message(
        chat_id=chat_id,
        text="📸 Análise de fotos está disponível apenas nos planos Pro e Premium.",
    )
    return
```

- [ ] **Step 6: Rodar testes do task**

Run: `cd backend && .venv/bin/pytest tests/unit/services/test_telegram_service.py -v`
Expected: PASS para texto e foto (permitido/bloqueado).

- [ ] **Step 7: Commit**

```bash
git add backend/src/services/telegram_service.py backend/tests/unit/services/test_telegram_service.py
git commit -m "feat: support telegram photo analysis with plan gating"
```

---

### Task 4: Upload de Imagem no Chat do App (Frontend)

**Files:**
- Modify: `frontend/src/shared/types/chat.ts`
- Modify: `frontend/src/shared/hooks/useChat.ts`
- Modify: `frontend/src/features/chat/components/ChatView.tsx`
- Test: `frontend/src/shared/hooks/useChat.test.ts`
- Test: `frontend/src/features/chat/components/ChatView.test.tsx`

- [ ] **Step 1: Escrever teste falhando do store para enviar texto+imagem**

```ts
// frontend/src/shared/hooks/useChat.test.ts
it('sends message with image payload when provided', async () => {
  await useChatStore.getState().sendMessage('Analisa essa foto', {
    base64: 'abc123',
    mimeType: 'image/jpeg',
  });

  expect(fetch).toHaveBeenCalledWith(
    expect.stringContaining('/message'),
    expect.objectContaining({
      body: JSON.stringify({
        user_message: 'Analisa essa foto',
        image_base64: 'abc123',
        image_mime_type: 'image/jpeg',
      }),
    })
  );
});
```

- [ ] **Step 2: Rodar teste e confirmar falha**

Run: `cd frontend && npm test -- useChat.test.ts`
Expected: FAIL porque assinatura atual de `sendMessage` só aceita texto.

- [ ] **Step 3: Implementar contrato de imagem no store/tipos**

```ts
// frontend/src/shared/types/chat.ts
export interface MessageImagePayload {
  base64: string;
  mimeType: 'image/jpeg' | 'image/png' | 'image/webp';
}

export interface MessageRequest {
  user_message: string;
  image_base64?: string;
  image_mime_type?: MessageImagePayload['mimeType'];
}
```

```ts
// frontend/src/shared/hooks/useChat.ts
sendMessage: async (text: string, image?: MessageImagePayload) => {
  ...
  body: JSON.stringify({
    user_message: text,
    image_base64: image?.base64,
    image_mime_type: image?.mimeType,
  })
}
```

- [ ] **Step 4: Escrever teste falhando de UI (upload + preview + envio)**

```ts
// frontend/src/features/chat/components/ChatView.test.tsx
it('allows selecting an image and calls onSend with attachment', async () => {
  // render ChatView com botão de upload
  // selecionar arquivo image/jpeg
  // esperar preview
  // submit form
  // assert onSend chamado com payload de imagem
});
```

- [ ] **Step 5: Implementar UI no ChatView**

```tsx
// frontend/src/features/chat/components/ChatView.tsx
<input
  data-testid="chat-image-input"
  type="file"
  accept="image/jpeg,image/png,image/webp"
  onChange={handleImageSelect}
/>
{selectedImage && <img src={selectedImage.previewUrl} alt="preview" />}
```

- [ ] **Step 6: Tratar erro de entitlement no frontend**

```ts
// frontend/src/shared/hooks/useChat.ts
if (errorData.detail === 'IMAGE_NOT_ALLOWED_FOR_PLAN') {
  throw new Error('IMAGE_NOT_ALLOWED_FOR_PLAN');
}
```

- [ ] **Step 7: Rodar testes do task**

Run: `cd frontend && npm test -- useChat.test.ts ChatView.test.tsx`
Expected: PASS para fluxo com/sem imagem + erro de plano.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/shared/types/chat.ts frontend/src/shared/hooks/useChat.ts frontend/src/features/chat/components/ChatView.tsx frontend/src/shared/hooks/useChat.test.ts frontend/src/features/chat/components/ChatView.test.tsx
git commit -m "feat: add multimodal image upload to app chat"
```

---

### Task 5: Atualizar Copy de Planos (Landing + Configurações)

**Files:**
- Modify: `frontend/src/locales/pt-BR.json`
- Modify: `frontend/src/locales/en-US.json`
- Modify: `frontend/src/locales/es-ES.json`
- Test: `frontend/src/features/landing/components/Pricing.test.tsx`
- Test: `frontend/src/features/settings/components/SubscriptionPage.test.tsx`

- [ ] **Step 1: Escrever teste falhando para novo texto de Pro/Premium**

```ts
// frontend/src/features/landing/components/Pricing.test.tsx
it('renders pro and premium copy mentioning photo analysis in chat and telegram', () => {
  render(<Pricing />);
  expect(screen.getByText(/foto|photo|foto/i)).toBeInTheDocument();
  expect(screen.getByText(/telegram/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Rodar teste e confirmar falha**

Run: `cd frontend && npm test -- Pricing.test.tsx SubscriptionPage.test.tsx`
Expected: FAIL porque copy atual não explicita análise de foto no chat + Telegram.

- [ ] **Step 3: Atualizar i18n de Pro/Premium em 3 idiomas**

```json
// exemplo em pt-BR.json
"pro": {
  "description": "Análise de fotos no chat e Telegram, com personalização avançada.",
  "features": ["Análise de fotos (chat + Telegram)", "Todos os mentores", "TDEE dinâmico"]
}
```

- [ ] **Step 4: Validar que SubscriptionPage consome os mesmos keys**

```tsx
// frontend/src/features/settings/components/SubscriptionPage.tsx
features: t('landing.plans.items.pro.features', { returnObjects: true }) as string[]
```

- [ ] **Step 5: Rodar testes do task**

Run: `cd frontend && npm test -- Pricing.test.tsx SubscriptionPage.test.tsx`
Expected: PASS para contrato de copy nas páginas de landing e assinatura.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/locales/pt-BR.json frontend/src/locales/en-US.json frontend/src/locales/es-ES.json frontend/src/features/landing/components/Pricing.test.tsx frontend/src/features/settings/components/SubscriptionPage.test.tsx
git commit -m "feat: update pro and premium copy for image analysis benefit"
```

---

### Task 6: Verificação Final e Gates Obrigatórios

**Files:**
- No new files.

- [ ] **Step 1: Rodar testes backend tocados**

Run: `cd backend && .venv/bin/pytest tests/test_subscription_plan_config.py tests/unit/api/test_message_endpoints.py tests/unit/services/test_trainer_streaming.py tests/unit/services/test_telegram_service.py -v`
Expected: PASS.

- [ ] **Step 2: Rodar lint backend obrigatório do AGENTS.md**

Run: `cd backend && .venv/bin/ruff check src tests && .venv/bin/pylint src`
Expected: PASS sem warnings em arquivos tocados.

- [ ] **Step 3: Rodar testes frontend tocados**

Run: `cd frontend && npm test -- useChat.test.ts ChatView.test.tsx Pricing.test.tsx SubscriptionPage.test.tsx`
Expected: PASS.

- [ ] **Step 4: Rodar lint/typecheck frontend obrigatório do AGENTS.md**

Run: `cd frontend && npm run lint && npm run typecheck`
Expected: PASS.

- [ ] **Step 5: Rodar gate rápido do projeto**

Run: `make verify`
Expected: PASS.

- [ ] **Step 6: Commit final de integração**

```bash
git add backend frontend
git commit -m "feat: enable image analysis in app chat and telegram for pro/premium"
```

---

## Spec Coverage Check

- Enviar foto para análise via chat app: coberto em Task 4 + Task 2.
- Enviar foto para análise via Telegram: coberto em Task 3 + Task 2.
- Restrito a PRO e Premium: coberto em Task 1 e reaplicado em Task 3.
- Atualizar descrição de assinatura em landing e configurações: coberto em Task 5.
- TDD: todos os tasks começam com teste falhando antes de implementação.
- Validações de lint/typecheck: coberto em Task 6.

## Placeholder Scan

- Sem TODO/TBD.
- Todos os tasks têm arquivos, comandos e resultados esperados.

## Consistency Check

- Erro de entitlement padronizado: `IMAGE_NOT_ALLOWED_FOR_PLAN` (backend + frontend).
- Contrato de imagem padronizado: `image_base64` + `image_mime_type`.
- Reutilização de copy via `landing.plans.items.*` preservada para landing e settings.
