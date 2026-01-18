# Future Career
 
 
 Full-stack приложение для проведения технических интервью: веб-IDE, генерация задач, оценка решений, античит-проверки и административные сценарии.
 
 **Основной интерфейс:** http://localhost:5173
---

 ## Быстрый старт

```bash
git clone <repo-url>
cd EXALAA
docker compose up -d --build
```

 После запуска будут доступны:

 | Сервис        | URL                        | Назначение                              |
 |---------------|---------------------------|-----------------------------------------|
 | Frontend      | http://localhost:5173     | Web UI (IDE, контест, админка)          |
 | Backend API   | http://localhost:8000/api | Основной API                            |
 | Swagger       | http://localhost:8000/docs| Документация API                        |
 | Executor      | http://localhost:8001     | Запуск пользовательского кода           |
 | ML Service    | http://localhost:8002     | Генерация/оценка задач и античит        |
 | Mailhog       | http://localhost:8025     | Тестовые письма (OTP/уведомления)       |

 `docker compose` автоматически поднимает инфраструктуру, выполняет миграции и прогоняет сидер (`backend/scripts/bootstrap_seed.py`).
 
 Остановить всё:
 
 ```bash
 docker compose down
 ```

---

 ## Архитектура

| Блок     | Технологии                         | Что делает                                                              |
|----------|------------------------------------|-------------------------------------------------------------------------|
| Backend  | FastAPI, SQLAlchemy async, Alembic | Auth, IDE API, пост-submit пайплайн, связь с ML и executor              |
| Executor | FastAPI + Docker SDK               | Запускает пользовательский код в изолированных контейнерах             |
| ML       | FastAPI                            | Генерация задач, оценка решений, анти-чит, follow-up чат, адаптивность |
| Frontend | React 19, Vite, TypeScript         | Веб-IDE, админка, контест, чат                                          |
| Infra    | Postgres 16, Mailhog               | База данных и тестовая почта                                            |

---

 ## Полезные команды

```bash
# Пересобрать и поднять
docker compose up -d --build

# Запустить скрипт базовой инициализации
docker compose exec backend python scripts/init_data.py

# Остановить с очисткой volume
docker compose down -v

# Логи сервиса
docker compose logs backend -f

# Повторно прогнать сидер (если нужно пустую базу)
docker compose run --rm backend python scripts/bootstrap_seed.py
```

---

 ## Проверка после запуска

1. Frontend на `:5173` открывается, OTP приходит в Mailhog.
2. Swagger на `:8000/docs` отвечает (проверить `/auth`, `/tasks`).
3. `docker compose ps` показывает все контейнеры в статусе `Up`.

---

 ## Структура репозитория

```
 backend/   # FastAPI + миграции, сидер bootstrap_seed.py
 executor/  # сервис выполнения кода
 ml/        # ML сервис (генерация задач, оценка, античит)
 frontend/  # React/Vite интерфейс (IDE + админка)
 docker-compose.yml
```

---

 ## Swagger

 Полная документация API доступна по адресу **http://localhost:8000/docs**.

---

 ## Почта

 Mailhog (http://localhost:8025) показывает все тестовые письма: OTP для входа и системные уведомления.

