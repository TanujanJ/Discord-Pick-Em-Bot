# Discord Pick 'Em Bot

## Description

An asynchronous multi-sport Discord pick 'em bot built by combining discord.py, FastAPI, and PostgreSQL. It allows users to register,
scroll through upcoming games in multiple leagues, predict the result of those games, and compare their scores with others through league leaderboards.
Game information is automatically obtained through ESPN's APIs. Games and leagues can be manually added through the API-key-protected FastAPI admin
backend. The FastAPI backend is also used to update game results, evaluate user predictions, and automatically update user scores.

## Prerequisites

- Python 3.14
- PostgreSQL
- Discord bot token
  - Server members intent turned on
  - Message content intent turned on
  - (Discord bot token and intents can be found in the Discord Developer Portal)

## Setup

#### Create a virtual environment

```bash
python -m venv .venv
```

#### Activate the virtual environment 

Windows: <br>
```bash
.venv\Scripts\activate
```

macOS/Linux <br>
```bash
source .venv/bin/activate
```

#### Install dependencies

```bash
pip install -r requirements.txt
```

#### Environment variables

Create a `.env` file and fill it with variables given in `.env.example`

#### Database setup

Create a PostgreSQL database matching the configuration in your `.env` file, then apply the database migrations:

```bash
alembic upgrade head
```

#### Running the application in development mode

```bash
uvicorn main:app --reload
```

## Discord commands

```md
- `!register` — Register with the bot
- `!leagues` — View available leagues
- `!games <league_name>` — View upcoming games and their IDs
- `!predict <game_id> "<team>"` — Submit a prediction
- `!leaderboard <league_name>` — View the server leaderboard for a league
```

## Example Use

<img width="704" height="490" alt="image" src="https://github.com/user-attachments/assets/728d2e96-46de-43d8-82f2-5ca3fc4449d2" />
