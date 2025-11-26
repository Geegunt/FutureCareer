# VibeCode Jam IDE

Веб-приложение для программирования с авторизацией, опросом для резюме и админ-панелью.

> 📐 **Архитектура проекта:** см. [ARCHITECTURE.md](./ARCHITECTURE.md)

## ⚡ Быстрый старт (скопируйте и выполните)

### Windows (PowerShell):
```powershell
# 1. Запустите инфраструктуру
docker compose up -d

# 2. Backend
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy env.example .env
cd app
python -m alembic upgrade head
cd ..
uvicorn app.main:app --reload

# 3. В новом терминале - Frontend
cd frontend
copy env.example .env
npm install
npm run dev
```

### Linux/macOS:
```bash
# 1. Запустите инфраструктуру
docker compose up -d

# 2. Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
cd app
python -m alembic upgrade head
cd ..
uvicorn app.main:app --reload

# 3. В новом терминале - Frontend
cd frontend
cp env.example .env
npm install
npm run dev
```

**Готово!** Откройте http://localhost:5173 в браузере.

---

## 📖 Подробная инструкция

### Требования

- **Python 3.11+** (для backend)
- **Node.js 18+** (для frontend)
- **Docker & Docker Compose** (для PostgreSQL и Mailhog)

### Шаг 1: Клонирование и настройка

```bash
# Клонируйте репозиторий (если еще не клонирован)
git clone <repository-url>
cd VibeCode-Jam
```

### Шаг 2: Запуск инфраструктуры (PostgreSQL + Mailhog)

```bash
# Запустите Docker Compose
docker compose up -d

# Проверьте, что контейнеры запущены
docker compose ps
```

### Шаг 3: Настройка Backend

#### Windows (PowerShell или CMD):
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy env.example .env
cd app
python -m alembic upgrade head
cd ..
uvicorn app.main:app --reload
```

#### Linux/macOS:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env
cd app
python -m alembic upgrade head
cd ..
uvicorn app.main:app --reload
```

**Backend будет доступен на:** http://localhost:8000

**API документация:** http://localhost:8000/docs

### Шаг 4: Настройка Frontend

#### Windows (PowerShell или CMD):
```powershell
cd frontend
copy env.example .env
npm install
npm run dev
```

#### Linux/macOS:
```bash
cd frontend
cp env.example .env
npm install
npm run dev
```

**Frontend будет доступен на:** http://localhost:5173

### Шаг 5: Проверка работы

1. Откройте http://localhost:5173 в браузере
2. Введите email и запросите код для входа
3. Проверьте код в Mailhog: http://localhost:8025
4. Введите код и войдите в систему

## 📧 Mailhog (Тестовая почта)

Mailhog используется для тестирования отправки email. Все письма можно просмотреть в веб-интерфейсе:

**Веб-интерфейс Mailhog:** http://localhost:8025

## 🔧 Настройка переменных окружения

### Backend (`.env` в папке `backend/`)

Скопируйте `env.example` в `.env` и при необходимости измените:

```env
APP_NAME=VibeCode IDE API
API_V1_STR=/api
SECRET_KEY=CHANGE_ME_SUPER_SECRET  # Измените на случайную строку!
ACCESS_TOKEN_EXPIRE_MINUTES=60

DATABASE_URL=postgresql+asyncpg://vibecode_jam:vibecode_jam@localhost:5432/vibecode_jam

SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=ide@vibecode.local
SMTP_TLS=False
```

### Frontend (`.env` в папке `frontend/`)

Скопируйте `env.example` в `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

## 👤 Назначение администратора

Чтобы сделать пользователя администратором, выполните SQL запрос:

```bash
# Windows (PowerShell)
docker compose exec postgres psql -U vibecode_jam -d vibecode_jam -c "UPDATE users SET is_admin = true WHERE email = 'your-email@example.com';"

# Linux/macOS
docker compose exec postgres psql -U vibecode_jam -d vibecode_jam -c "UPDATE users SET is_admin = true WHERE email = 'your-email@example.com';"
```

Или через любой PostgreSQL клиент подключитесь к базе и выполните:
```sql
UPDATE users SET is_admin = true WHERE email = 'your-email@example.com';
```

## 📁 Структура проекта

```
VibeCode-Jam/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── alembic/      # Миграции базы данных
│   │   ├── core/         # Конфигурация, безопасность
│   │   ├── models/       # SQLAlchemy модели
│   │   ├── routes/       # API роуты
│   │   ├── schemas/      # Pydantic схемы
│   │   └── services/    # Бизнес-логика, CRUD
│   ├── env.example       # Пример конфигурации
│   └── requirements.txt # Python зависимости
├── frontend/             # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/   # React компоненты
│   │   └── modules/      # Модули (auth, questions, admin)
│   ├── env.example       # Пример конфигурации
│   └── package.json      # Node.js зависимости
└── docker-compose.yml    # Docker конфигурация
```

## 🗄️ Миграции базы данных

Проект использует Alembic для управления миграциями. **Миграции применяются автоматически при первом запуске** (см. инструкции выше).

### Применение миграций вручную

#### Windows:
```powershell
cd backend\app
python -m alembic upgrade head
```

#### Linux/macOS:
```bash
cd backend/app
python -m alembic upgrade head
```

### Создание новой миграции

#### Windows:
```powershell
cd backend\app
python -m alembic revision --autogenerate -m "Описание изменений"
python -m alembic upgrade head
```

#### Linux/macOS:
```bash
cd backend/app
python -m alembic revision --autogenerate -m "Описание изменений"
python -m alembic upgrade head
```

## 🛠️ Разработка

### Backend

- **Технологии:** FastAPI, SQLAlchemy (async), PostgreSQL, Alembic, JWT
- **Порт:** 8000
- **Hot reload:** включен по умолчанию (`--reload`)

### Frontend

- **Технологии:** React 19, TypeScript, Vite, Monaco Editor
- **Порт:** 5173
- **Hot reload:** включен по умолчанию

## 🐛 Решение проблем

### Порт уже занят

Если порт 5432 (PostgreSQL) или 1025/8025 (Mailhog) заняты:

```bash
# Остановите контейнеры
docker compose down

# Или остановите конкретный контейнер
docker stop <container-name>
```

### Ошибка подключения к базе данных

Убедитесь, что:
1. Docker Compose запущен: `docker compose ps`
2. PostgreSQL контейнер работает
3. В `.env` правильный `DATABASE_URL`

### Ошибка "column does not exist"

Примените миграции:
```bash
cd backend/app
python -m alembic upgrade head
```

### Alembic не найден

Убедитесь, что виртуальное окружение активировано и зависимости установлены:
```bash
# Windows
.\venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
source venv/bin/activate
pip install -r requirements.txt
```

## 📝 API Endpoints

- `POST /api/auth/request-code` - Запрос кода для входа
- `POST /api/auth/verify` - Проверка кода и получение токена
- `GET /api/users/me` - Профиль текущего пользователя
- `GET /api/questions` - Список вопросов
- `POST /api/questions/{id}/answers` - Сохранение ответа
- `GET /api/admin/questions` - Управление вопросами (только админ)
- `GET /api/admin/answers` - Просмотр всех ответов (только админ)

Полная документация API доступна на http://localhost:8000/docs

## 📄 Лицензия

MIT

