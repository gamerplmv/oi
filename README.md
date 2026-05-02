# Lunar Bot (discord.py)

Bot estilo Carl-bot para autoroles com:
- Reações por emoji
- Select menu
- Botões
- Mensagens multilíngues (PT/EN)
- Proteção anti-dupla interação entre versões de idioma da mesma embed
- Persistência local com banco assíncrono (SQLite + SQLAlchemy asyncio)

## Setup
1. `python -m venv .venv && source .venv/bin/activate`
2. `pip install -e .`
3. Copie `.env.example` para `.env` e preencha `DISCORD_TOKEN`.
4. `python -m lunar_bot`

## Comandos
- `/rr_create_reaction`
- `/rr_create_select`
- `/rr_create_buttons`
- `/rr_link_translations`

> Recomendado: criar cargo e canais antes de configurar.
