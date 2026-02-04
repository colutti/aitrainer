# Token Expiration Manual Testing

## Objetivo
Validar que a detecção automática de expiração de sessão funciona corretamente sem interação do usuário.

## Pré-requisitos
- Backend rodando: `make up` ou `make restart`
- Frontend rodando: `npm run dev` em `frontend/`
- Navegador com DevTools aberto (F12)

## Teste 1: Verificar monitoramento com token curto

### Opção A: Modificar tempo de expiração no backend (5 minutos)

1. Editar `backend/src/core/config.py`:
```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = 1  # Reduzir para 1 minuto
```

2. Reiniciar backend:
```bash
make restart
```

3. Fazer login na aplicação

4. Abrir DevTools → Console
   - Esperar ver mensagens:
   ```
   Token expira em 60s. Timer agendado para 55s
   ```

5. Aguardar ~55 segundos (antes da expiração real)
   - Sem clicar em nada
   - Ver no console:
   ```
   Token expirado - disparando signal
   Token expirado detectado - fazendo logout automático
   ```

6. Verificar que a aplicação **automaticamente**:
   - Mostra tela de login
   - Limpa localStorage (DevTools → Application → LocalStorage)
   - Não fez nenhuma requisição HTTP com erro 401

7. Fazer login novamente para confirmar que funciona normalmente

8. Reverter `ACCESS_TOKEN_EXPIRE_MINUTES` para valor original

### Opção B: Modificar token manualmente (10 minutos)

1. Fazer login normalmente

2. DevTools → Application → LocalStorage → copiar token JWT

3. Acessar https://jwt.io:
   - Colar token no campo esquerdo
   - Modificar campo `exp` (linha 4):
     ```json
     "exp": 1770217500  // Mude para timestamp atual + 60s
     ```
   - Copiar token modificado

4. Voltar DevTools → Application → LocalStorage
   - Colar token modificado na chave `jwt_token`
   - Salvar

5. Recarregar página (F5)

6. Verificar console:
   - Esperar mensagens de monitoramento
   - Aguardar ~55 segundos
   - Ver logout automático

## Teste 2: Verificar fallback com ErrorInterceptor

1. Com token normal, fazer login

2. Abrir DevTools → Network

3. Clicar em qualquer botão que faça requisição HTTP

4. Se token estiver expirado:
   - Ver resposta 401 no Network
   - ErrorInterceptor também faz logout

## Teste 3: Verificar múltiplas abas

1. Fazer login em Aba 1

2. Abrir Aba 2 no mesmo app

3. Ambas as abas devem mostrar logout automático no mesmo momento

## Resultado Esperado

✅ **Sucesso** quando:
- Token expira sem nenhuma interação do usuário
- Logout dispara automaticamente baseado em timer
- Aplicação renderiza tela de login
- localStorage é limpo
- Novo login funciona normalmente
- Build de produção funciona sem erros

❌ **Falha** se:
- Usuário não é redirecionado para login
- Token não é removido de localStorage
- Novo login não funciona

## Checklist de Completude

- [ ] Instalação de jwt-decode bem-sucedida
- [ ] TokenExpirationService criado e injetado
- [ ] AuthService integrado (login, logout, loadUserInfo)
- [ ] AppComponent effect adicionado
- [ ] 8 unit tests passando
- [ ] 3 component tests passando
- [ ] Build frontend sem erros
- [ ] Teste manual Opção A bem-sucedido
- [ ] Teste manual Opção B bem-sucedido
- [ ] Logout automático funciona sem interação do usuário
- [ ] Login subsequente funciona normalmente

## Notas

- Se modificou `ACCESS_TOKEN_EXPIRE_MINUTES`, não esqueça de reverter!
- O timer dispara 5 segundos ANTES da expiração real (buffer de segurança)
- Se o timer falhar, ErrorInterceptor continua como fallback
- Console.logs podem ser removidos em produção se desejado
