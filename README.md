# Contmagnat

Telegram bot for generating posts from topic-based and channel-profile style examples.

## Stack

- Python 3.11
- aiogram v3
- FastAPI API endpoints
- Local file storage in `data/training`
- Anthropic-compatible generation through gngn/Ethereal

## Local Setup

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```

Fill `.env` locally. Do not commit it.

```env
TELEGRAM_BOT_TOKEN=your-telegram-token
ADMIN_PASSWORD=your-admin-password
STORAGE_BACKEND=file
TRAINING_DATA_DIR=data/training

TEXT_GENERATION_PROVIDER=anthropic
ANTHROPIC_BASE_URL=https://api.gngn.my
ANTHROPIC_AUTH_TOKEN=your-gngn-key
ANTHROPIC_MODEL=claude-opus-4-7
```

## Run

Bot:

```powershell
python -m app.bot.main
```

API:

```powershell
python -m app.main
```

Tests:

```powershell
python -m pytest -q
```

## Bot Flow

- `/start` opens the main menu.
- Admin login uses `ADMIN_PASSWORD`.
- Admin can add topics, create channel profiles, and save forwarded posts.
- Training posts are stored locally:
  - `data/training/topics/<topic>/posts.jsonl`
  - `data/training/profiles/<profile>/posts.jsonl`
- Local RAG indexes are rebuilt automatically:
  - `data/training/topics/<topic>/rag_index.json`
  - `data/training/profiles/<profile>/rag_index.json`
- User generation can use either a topic or an individual channel profile.
- Generation picks similar and fresh examples from the selected topic/profile and sends them to the model as style context.

## VPS Deploy With systemd

Install dependencies:

```bash
sudo apt update
sudo apt install -y git python3.11 python3.11-venv
```

Clone and install:

```bash
sudo mkdir -p /opt
sudo git clone https://github.com/caraxesq/contmagnat.git /opt/contmagnat
sudo chown -R "$USER:$USER" /opt/contmagnat
cd /opt/contmagnat
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env
```

Create `/etc/systemd/system/contmagnat-bot.service`:

```ini
[Unit]
Description=Contmagnat Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/opt/contmagnat
EnvironmentFile=/opt/contmagnat/.env
ExecStart=/opt/contmagnat/.venv/bin/python -m app.bot.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now contmagnat-bot
sudo journalctl -u contmagnat-bot -f
```
