# Contmagnat

Telegram RAG post generator MVP.

## Stack

- FastAPI
- aiogram v3
- PostgreSQL + pgvector
- OpenRouter integration points for future embeddings and generation

## Setup

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```

Put the Telegram token only into `.env`:

```env
TELEGRAM_BOT_TOKEN=your-token
STORAGE_BACKEND=memory
ALLOWED_TELEGRAM_USER_IDS=
```

If a bot token was posted in chat or committed anywhere, rotate it in BotFather.

`STORAGE_BACKEND=memory` is the default local mode. It runs without PostgreSQL and keeps data only while the process is alive.

## Run Without Docker

API:

```powershell
python -m app.main
```

Bot:

```powershell
python -m app.bot.main
```

You can also run the API directly:

```powershell
uvicorn app.api.main:app --reload
```

## Local API Test

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/generation" `
  -Method Post `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"topic":"кулинария","user_request":"пост про быстрый ужин"}'
```

Expected response contains:

```json
{
  "status": "ok",
  "generated_text": "Сгенерированный тестовый пост..."
}
```

## MVP Flow

- `/start` opens the main menu.
- `/generate пост про завтрак` runs a minimal e2e generation scenario.
- `Загрузить посты` asks for one of the topics: кулинария, отношения, здоровье, красота, дом, кастом.
- `Кастом` asks for a custom topic name.
- Posts are split by blank lines and saved to the configured storage backend.
- `Сгенерировать пост` collects topic and request, logs the request, and returns generated text.
- If OpenRouter env vars are empty, generation uses a local mock response.

## OpenRouter and pgvector

- `app/clients/openrouter.py` is the only OpenRouter HTTP client.
- `app/services/embeddings.py` will call OpenRouter embeddings.
- `app/services/generation.py` calls a text generator; `app/services/text_generation.py` chooses OpenRouter when configured, otherwise mock.
- `posts.embedding` is a pgvector column.
- `PostsRepository.find_similar` performs pgvector cosine similarity search.

## PostgreSQL Mode

PostgreSQL is optional for local e2e testing. To enable it later:

```env
STORAGE_BACKEND=postgres
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/contmagnat
```

Then run:

```powershell
docker compose up -d postgres
alembic upgrade head
```
