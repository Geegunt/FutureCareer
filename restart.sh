#!/usr/bin/env bash
# Безопасный перезапуск приложения без зависания

set -e

echo "🛑 Останавливаем все контейнеры..."
docker compose down --remove-orphans 2>/dev/null || true

echo "🧹 Очищаем старые образы и контейнеры..."
docker system prune -f 2>/dev/null || true

echo "🔨 Пересобираем образы..."
docker compose build --no-cache

echo "🚀 Запускаем сервисы..."
docker compose up -d

echo "⏳ Ожидание запуска сервисов (30 секунд)..."
sleep 30

echo "✅ Сервисы запущены!"
echo ""
echo "Доступные URL:"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000/api"
echo "  Swagger:   http://localhost:8000/docs"
echo "  Executor:  http://localhost:8001"
echo "  ML:        http://localhost:8002"
echo "  Mailhog:   http://localhost:8025"
echo ""
echo "Для просмотра логов используйте:"
echo "  docker compose logs -f [service_name]"
echo ""
echo "Доступные сервисы: backend, executor, ml, frontend, postgres, mailhog"
