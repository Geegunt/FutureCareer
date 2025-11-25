# Backend (FastAPI)

Сервис отвечает за авторизацию пользователей, выдачу одноразовых кодов, отправку e-mail через Mailhog и предоставление данных личного кабинета для IDE.

## Быстрый старт

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Перед запуском создайте файл `.env` на основе `env.example` и поднимите инфраструктуру:

```bash
docker compose up -d
```

## Основные зависимости

- FastAPI + Pydantic Settings
- SQLAlchemy (async) + PostgreSQL
- aiosmtplib для отправки почты (Mailhog)
- JWT токены (`python-jose`)

## Структура

```
app/
  core/        # конфигурация, безопасность
  database.py  # engine + session
  models/      # SQLAlchemy модели
  routes/      # роуты FastAPI
  services/    # почта, auth-логика
  schemas/     # pydantic-схемы
```

При первом старте таблицы создаются автоматически. В проде рекомендуется добавить миграции (Alembic).  
Личные данные пользователей и одноразовые коды хранятся в PostgreSQL, логин-коды автоматически истекают через 10 минут.

