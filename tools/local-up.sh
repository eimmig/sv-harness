#!/usr/bin/env bash
# Sobe ambiente de teste local completo: infra (Docker Compose) + build e start dos
# 4 servicos Java, telegram-integration (Python) e web (Angular dev server).
#
# Nao e parte do gate formal de nenhum harness (init.sh continua sendo a verificacao
# que conta para Definicao de Pronto) - e so conveniencia pra rodar tudo junto com um
# comando, ja que infra/docker-compose.yml so declara infraestrutura (Postgres x3,
# RabbitMQ, Redis, n8n), nunca os servicos de aplicacao (cada um e repo/build proprio).
#
# Uso: bash tools/local-up.sh
# Para derrubar: bash tools/local-down.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"
LOG_DIR="$ROOT_DIR/tools/.local-run"
PID_FILE="$LOG_DIR/pids"

mkdir -p "$LOG_DIR"
: > "$PID_FILE"

# --- 1. infra/.env: cria a partir do example se faltar, garante segredos extras ---
if [[ ! -f "$INFRA_DIR/.env" ]]; then
  cp "$INFRA_DIR/.env.example" "$INFRA_DIR/.env"
  echo "criei infra/.env a partir do .env.example (senhas default - troque se for compartilhar o ambiente)"
fi

rand_hex() { openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'; }

ensure_var() {
  local name="$1"
  if ! grep -q "^${name}=" "$INFRA_DIR/.env"; then
    echo "${name}=$(rand_hex)" >> "$INFRA_DIR/.env"
  fi
}
# Segredos compartilhados entre servicos (auth-service assina PASETO, api-gateway
# valida com a mesma chave; SERVICE_KEY e o header que api-gateway/telegram-integration
# trocam com os servicos internos; ADMIN_API_KEY protege os endpoints /admin).
ensure_var PASETO_LOCAL_KEY
ensure_var SERVICE_KEY
ensure_var ADMIN_API_KEY

set -a
source "$INFRA_DIR/.env"
set +a

# --- 2. sobe infra ---
echo "== infra: docker compose up =="
(cd "$INFRA_DIR" && docker compose up -d)

echo "== infra: aguardando containers healthy =="
for svc in postgres-auth postgres-bets postgres-stats rabbitmq redis; do
  container="stakevault-infra-${svc}-1"
  tries=0
  until [[ "$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null)" = "healthy" ]]; do
    tries=$((tries + 1))
    if [[ "$tries" -gt 60 ]]; then
      echo "FALHOU: $svc nao ficou healthy em 2min - ver 'docker logs $container'"
      exit 1
    fi
    sleep 2
  done
  echo "OK   $svc healthy"
done

# --- 3. build + start dos servicos Java (auth, bets, stats) ---
start_java_service() {
  local name="$1" port="$2" db_port="$3" db_name="$4" db_user="$5" db_pass="$6"
  echo "== $name: build (mvn package) =="
  (cd "$ROOT_DIR/services/$name" && ./mvnw -q -DskipTests package)
  local jar
  jar="$(ls "$ROOT_DIR/services/$name"/target/*.jar | grep -v -e sources -e original | head -1)"
  echo "== $name: start na porta $port =="
  DB_HOST=localhost DB_PORT="$db_port" DB_NAME="$db_name" DB_USER="$db_user" DB_PASSWORD="$db_pass" \
  RABBITMQ_USER="$RABBITMQ_USER" RABBITMQ_PASSWORD="$RABBITMQ_PASSWORD" \
  REDIS_PASSWORD="$REDIS_PASSWORD" \
  PASETO_LOCAL_KEY="$PASETO_LOCAL_KEY" SERVICE_KEY="$SERVICE_KEY" ADMIN_API_KEY="$ADMIN_API_KEY" \
  java -jar "$jar" --spring.profiles.active=dev > "$LOG_DIR/$name.log" 2>&1 &
  echo "$name:$!" >> "$PID_FILE"
}

start_java_service auth-service  8081 5432 "$POSTGRES_AUTH_DB"  "$POSTGRES_AUTH_USER"  "$POSTGRES_AUTH_PASSWORD"
start_java_service bets-service  8082 5433 "$POSTGRES_BETS_DB"  "$POSTGRES_BETS_USER"  "$POSTGRES_BETS_PASSWORD"
start_java_service stats-service 8083 5434 "$POSTGRES_STATS_DB" "$POSTGRES_STATS_USER" "$POSTGRES_STATS_PASSWORD"

# --- 4. build + start do api-gateway (sem banco proprio) ---
echo "== api-gateway: build (mvn package) =="
(cd "$ROOT_DIR/services/api-gateway" && ./mvnw -q -DskipTests package)
gateway_jar="$(ls "$ROOT_DIR/services/api-gateway"/target/*.jar | grep -v -e sources -e original | head -1)"
echo "== api-gateway: start na porta 8080 =="
PASETO_LOCAL_KEY="$PASETO_LOCAL_KEY" SERVICE_KEY="$SERVICE_KEY" \
AUTH_SERVICE_URL="http://localhost:8081" BETS_SERVICE_URL="http://localhost:8082" STATS_SERVICE_URL="http://localhost:8083" \
java -jar "$gateway_jar" > "$LOG_DIR/api-gateway.log" 2>&1 &
echo "api-gateway:$!" >> "$PID_FILE"

# --- 5. build + start do telegram-integration ---
echo "== telegram-integration: build (uv sync) =="
(cd "$ROOT_DIR/services/telegram-integration" && uv sync --no-build)
echo "== telegram-integration: start na porta 8000 =="
(
  cd "$ROOT_DIR/services/telegram-integration"
  REDIS_PASSWORD="$REDIS_PASSWORD" SERVICE_KEY="$SERVICE_KEY" \
  uv run --no-build telegram-integration > "$LOG_DIR/telegram-integration.log" 2>&1 &
  echo "telegram-integration:$!" >> "$PID_FILE"
)

# --- 6. build + start do web (ng serve) ---
if [[ ! -d "$ROOT_DIR/apps/web/node_modules" ]]; then
  echo "== web: npm ci =="
  (cd "$ROOT_DIR/apps/web" && npm ci --ignore-scripts)
fi
echo "== web: start na porta 4200 =="
(
  cd "$ROOT_DIR/apps/web"
  npx --ignore-scripts ng serve > "$LOG_DIR/web.log" 2>&1 &
  echo "web:$!" >> "$PID_FILE"
)

cat <<EOF

Ambiente no ar:
  api-gateway            http://localhost:8080
  auth-service            http://localhost:8081
  bets-service            http://localhost:8082
  stats-service           http://localhost:8083
  telegram-integration    http://localhost:8000
  web                     http://localhost:4200
  rabbitmq (console)      http://localhost:15672
  n8n                     http://localhost:5678

Logs:  $LOG_DIR/<servico>.log
PIDs:  $PID_FILE
Parar: bash tools/local-down.sh
EOF
