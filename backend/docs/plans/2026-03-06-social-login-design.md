# Firebase Social Login - Design Document

## 1. Contexto e Objetivo
Implementar o fluxo de autenticação via Login Social (foco inicial no Google) para facilitar o acesso de novos e atuais usuários, melhorando a taxa de conversão do sistema FityQ. A arquitetura escolhida utiliza o Firebase Authentication como provedor de identidade no frontend e validador no backend, abrindo caminho para adicionar provedores como Apple e Facebook no futuro com esforço mínimo.

## 2. Requisitos Definidos
- **Frontend Experiência:** Adicionar botão de "Continuar com Google" na `LoginPage`.
- **Backend Arquitetura:** O backend valida o token JWT gerado pelo Firebase e gera um JWT nativo da aplicação. Desta forma, o resto da arquitetura não precisa saber da existência do Firebase.
- **Criação Automática:** Se for o primeiro acesso do usuário (e-mail não existe no banco), ele deve ser criado automaticamente no **Plano Grátis**, recebendo os dados do Google (nome e foto) e atributos físicos "default" que permitirão a inicialização do app sem formulários de onboarding (sendo configuráveis posteriormente no perfil do usuário).

## 3. Arquitetura e Fluxo de Dados

### 3.1. Frontend (React + Vite)
1. Precisamos instalar a dependência `firebase` no frontend.
2. Criar um arquivo de configuração `src/features/auth/firebase.ts` com as chaves recebidas do Firebase Console do FityQ.
3. No hook `useAuthStore`, adicionar uma nova action `socialLogin(provider: string)`.
   - Essa action chama `signInWithPopup(auth, provider)` do SDK do Firebase.
   - Pega o `idToken` resultante da promise.
   - Envia um `POST /user/social-login` com `{ "token": "<ID_TOKEN_DO_FIREBASE>" }`.
   - Salva o JWT retornado pela nossa API no `localStorage` como já faz hoje no login tradicional.

### 3.2. Backend (FastAPI + MongoDB)
1. Instalar a dependência `firebase-admin` no backend.
2. Inicializar o Firebase Admin SDK (ex: `src/core/firebase.py`) usando a `FIREBASE_CREDENTIALS` (Service Account JSON) via variável de ambiente.
3. Criar uma nova rota em `src/api/endpoints/user.py`: `POST /social-login`.
   - Rota recebe o token do frontend.
   - Valida o token usando `firebase_admin.auth.verify_id_token`.
   - Extrai o e-mail, nome e picture (foto).
4. **Regra de Negócio (O pulo do gato):**
   - Com o e-mail em mãos, consultar `brain.get_user_profile(email)`.
   - **Caso Exista:** Apenas atualizar `display_name` e `photo_base64` se eles estiverem vazios.
   - **Caso NÃO Exista:** Criar um novo `UserProfile` com o e-mail do Google. Como o nosso modelo de `UserProfile` exige dados físicos (para o funcionamento dos prompts e cálculos de TDEE), faremos o bypass utilizando valores padrão:
     - `subscription_plan`: "Free"
     - `role`: "user"
     - `gender`: "Masculino" (valor padrão aceito pelo regex)
     - `age`: 30
     - `weight`: 70.0
     - `height`: 170
     - `goal_type`: "maintain"
     - `display_name`: O nome que veio do Google.
     - `photo_base64`: A URL da foto (ou deixamos vazia se o modelo só aceitar base64, embora possamos colocar a URL para ser exibida e baixada depois/frontend tratar). Como o campo foi desenhado para base64 (`max_length=700_000`), podemos ter que lidar com isso no frontend (só renderizar) ou salvar a URL no campo foto se fizermos bypass da tipagem (o ideal é baixar a foto e converter em base64 ou armazenar a URL). *Decisão: armazena a URL no campo `photo_base64` (vamos ignorar o prefixo base64 se for uma URL http).*
     - Criaremos o `TrainerProfile` e o `WeightLog` inicial, tal como no Onboarding.
   - Gerar e retornar o JWT tradicional da aplicação chamando a função `create_token(email)`.

## 4. Alterações de Banco de Dados
A modelagem atual é flexível. O `UserProfile` já possui `display_name` e `photo_base64`. Não há necessidade absoluta de adicionar um `auth_provider` rígido agora, pois baseamos toda a identidade no email (Primary Key natural do sistema). Contudo, se tentarem fazer login com senha num email social que não tem senha cadastrada, a API retornará 401. Para isso, o campo `password_hash` do `UserProfile` já é `Optional`.

## 5. Passos para a Segurança Ativa
* O `FIREBASE_CREDENTIALS` no backend é uma string JSON do SDK de serviço ou apenas o path, tem que ser lida com segurança.
* As chaves do client-side do Firebase são públicas (não confidenciais), então colocar no `.env` do frontend é plenamente seguro.

---
**Status:** Aprovado. Seguindo para a criação do plano de implementação tático de código `writing-plans`.
