#!/bin/bash

# Script de Deploy Automático no Render com Streaming de Logs
# Uso: ./scripts/render-deploy.sh [backend|frontend|all] [--clear-cache] [--no-logs]

set -e

# IDs dos serviços
BACKEND_ID="srv-d5f2utqli9vc73dak390"
FRONTEND_ID="srv-d5f3e8u3jp1c73bkjbf0"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Variáveis
SERVICE="${1:-all}"
CLEAR_CACHE=""
STREAM_LOGS="yes"

# Processar argumentos
shift || true
for arg in "$@"; do
  if [ "$arg" = "--clear-cache" ]; then
    CLEAR_CACHE="--clear-cache"
  elif [ "$arg" = "--no-logs" ]; then
    STREAM_LOGS="no"
  fi
done

# Função para fazer deploy
deploy_service() {
  local service_id=$1
  local service_name=$2

  echo -e "${BLUE}═══════════════════════════════════════${NC}"
  echo -e "${BLUE}🚀 Iniciando deploy: ${YELLOW}${service_name}${NC}"
  echo -e "${BLUE}═══════════════════════════════════════${NC}"

  if [ -n "$CLEAR_CACHE" ]; then
    echo -e "${YELLOW}⚠️  Cache será limpo antes do build${NC}"
  fi

  if [ "$STREAM_LOGS" = "yes" ]; then
    echo -e "${CYAN}📡 Streaming de logs ativo${NC}"
  fi

  echo ""

  # Disparar deploy com wait (logs são streamados automaticamente)
  if render deploys create "$service_id" \
    --confirm \
    --wait \
    $CLEAR_CACHE; then

    echo ""
    echo -e "${GREEN}✅ Deploy de ${service_name} concluído com sucesso!${NC}"
    return 0
  else
    echo ""
    echo -e "${RED}❌ Deploy de ${service_name} falhou!${NC}"
    return 1
  fi
}

# Função para fazer streaming de logs em tempo real
stream_logs() {
  local service_id=$1
  local service_name=$2

  echo -e "${CYAN}═══════════════════════════════════════${NC}"
  echo -e "${CYAN}📡 Streaming de logs: ${YELLOW}${service_name}${NC}"
  echo -e "${CYAN}═══════════════════════════════════════${NC}"
  echo -e "${CYAN}Pressione Ctrl+C para parar${NC}"
  echo ""

  render logs \
    --resources "$service_id" \
    --tail \
    --output text
}

# Validar que o usuário está autenticado
if ! render whoami --output json > /dev/null 2>&1; then
  echo -e "${RED}❌ Erro: Você não está autenticado no Render${NC}"
  echo -e "${YELLOW}Execute: render login${NC}"
  exit 1
fi

echo -e "${BLUE}🔐 Autenticado como: $(render whoami --output json | jq -r '.email' 2>/dev/null || echo 'Desconhecido')${NC}"
echo ""

# Executar baseado no argumento
case "$SERVICE" in
  backend)
    deploy_service "$BACKEND_ID" "aitrainer-backend" || exit 1
    ;;
  frontend)
    deploy_service "$FRONTEND_ID" "aitrainer-frontend" || exit 1
    ;;
  all)
    echo -e "${BLUE}🔄 Iniciando deploy de todos os serviços...${NC}"
    echo ""

    deploy_service "$BACKEND_ID" "aitrainer-backend" || {
      echo -e "${RED}❌ Deploy do backend falhou. Abortando.${NC}"
      exit 1
    }

    echo ""
    sleep 2

    deploy_service "$FRONTEND_ID" "aitrainer-frontend" || {
      echo -e "${RED}❌ Deploy do frontend falhou.${NC}"
      exit 1
    }

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Todos os deploys foram concluídos!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    ;;
  stream-logs-backend)
    stream_logs "$BACKEND_ID" "aitrainer-backend"
    ;;
  stream-logs-frontend)
    stream_logs "$FRONTEND_ID" "aitrainer-frontend"
    ;;
  *)
    echo -e "${RED}❌ Uso inválido: $SERVICE${NC}"
    echo ""
    echo "🚀 DEPLOY:"
    echo "  ./scripts/render-deploy.sh backend              # Deploy apenas backend"
    echo "  ./scripts/render-deploy.sh frontend             # Deploy apenas frontend"
    echo "  ./scripts/render-deploy.sh all                  # Deploy de ambos"
    echo ""
    echo "📡 STREAMING DE LOGS:"
    echo "  ./scripts/render-deploy.sh stream-logs-backend  # Logs backend em tempo real"
    echo "  ./scripts/render-deploy.sh stream-logs-frontend # Logs frontend em tempo real"
    echo ""
    echo "Flags opcionais para deploy:"
    echo "  --clear-cache                                   # Limpar cache antes do build"
    echo "  --no-logs                                       # Desabilitar streaming de logs"
    echo ""
    echo "Exemplos:"
    echo "  ./scripts/render-deploy.sh all"
    echo "  ./scripts/render-deploy.sh backend --clear-cache"
    echo "  ./scripts/render-deploy.sh frontend --no-logs"
    echo "  ./scripts/render-deploy.sh stream-logs-backend"
    exit 1
    ;;
esac
