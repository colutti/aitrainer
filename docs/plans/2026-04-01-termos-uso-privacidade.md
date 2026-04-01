# Plano Enxuto: Termos de Uso e Privacidade

Data: 2026-04-01

## Objetivo

Publicar textos base de `Termos de Uso` e `Política de Privacidade` para o app, e garantir que a tela de login aponte para páginas públicas válidas.

## Escopo

1. Criar documento de Termos de Uso.
2. Criar documento de Política de Privacidade.
3. Incluir seção explícita sobre criptografia ponta a ponta:
   - ainda não implementada hoje;
   - requisito obrigatório antes de produção.
4. Criar rotas públicas no frontend para leitura desses conteúdos.
5. Atualizar links da página de login para as novas rotas.

## Fora de Escopo (agora)

1. Revisão jurídica formal.
2. Tradução para múltiplos idiomas.
3. Fluxo de aceite versionado por usuário.

## Decisões

1. Linguagem simples e direta, sem excesso de juridiquês.
2. Rotas públicas escolhidas:
   - `/termos-de-uso`
   - `/politica-de-privacidade`
3. Manter compatibilidade de links antigos com redirecionamento:
   - `/terms` -> `/termos-de-uso`
   - `/privacy` -> `/politica-de-privacidade`

