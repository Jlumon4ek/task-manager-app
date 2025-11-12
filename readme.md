## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone https://github.com/Jlumon4ek/task-manager-app.git
cd task-manager-app
```

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# JWT
ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=7

# PostgreSQL
POSTGRES_HOST=database
POSTGRES_PORT=5432
POSTGRES_DB=taskmanager_db
POSTGRES_USER=taskmanager_user
POSTGRES_PASSWORD=taskmanager_password

# PgAdmin
PGADMIN_EMAIL=admin@example.com
PGADMIN_PASSWORD=admin

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Email Backend
EMAIL_BACKEND=fake

```

### 3. Генерация RSA ключей (если не существуют)

Если папка `keys/` не содержит RSA ключи, создайте их:

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path keys
openssl genrsa -out keys/private_key.pem 2048
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem
```

**Linux/Mac:**
```bash
mkdir -p keys
openssl genrsa -out keys/private_key.pem 2048
openssl rsa -in keys/private_key.pem -pubout -out keys/public_key.pem
```

### 4. Запуск контейнеров

```bash
docker compose up -d --build
```

### 5. Применение миграций

```bash
docker exec -it backend python manage.py migrate
docker exec -it backend python manage.py migrate django_celery_beat

```


## Использование API

### Документация API
После запуска документация доступна по адресам:

- **Swagger UI**: http://localhost:8000/api/swagger/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### Основные endpoints

#### Аутентификация

```http
POST /api/v1/auth/signup/          # Регистрация
POST /api/v1/auth/signin/          # Вход
POST /api/v1/auth/token/refresh/   # Обновление токена
POST /api/v1/auth/logout/          # Выход
```

#### Задачи

```http
GET    /api/v1/tasks/              # Список задач (с фильтрацией и поиском)
POST   /api/v1/tasks/              # Создание задачи
GET    /api/v1/tasks/{id}/         # Детали задачи
PUT    /api/v1/tasks/{id}/         # Полное обновление
PATCH  /api/v1/tasks/{id}/         # Частичное обновление
DELETE /api/v1/tasks/{id}/         # Удаление задачи
```

#### Совместный доступ к задачам

```http
POST   /api/v1/tasks/{id}/share/   # Поделиться задачей
DELETE /api/v1/tasks/{id}/unshare/ # Отозвать доступ
GET    /api/v1/tasks/shared/       # Задачи, доступные мне
```



