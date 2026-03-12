# Testing SellScope Without Docker

You can test in two ways: **scraper only** (no database) or **full stack** with local PostgreSQL and Redis.

---

## Option 1: Scraper only (fastest)

No database or API. You only need Python and Chrome.

```bash
# 1. Go to scraper folder
cd scraper

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Run a small test (10 results, headless)
python3 adobe_stock_scraper.py "fruit" -n 10 --headless

# 4. Check output
ls -la output/
cat output/adobe_stock_fruit_*.csv
```

With full details and similar assets:

```bash
python3 adobe_stock_scraper.py "fruit" -n 10 --details --similar --max-similar 3 --headless
```

Results are in `scraper/output/` as CSV and (if you used `--json`) JSON. No Docker, no API, no DB.

---

## Option 2: Full stack (API + frontend) with local PostgreSQL and Redis

You need PostgreSQL and Redis running locally (e.g. via Homebrew on macOS).

### 1. Install PostgreSQL and Redis (macOS with Homebrew)

```bash
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
```

Create the database and user:

```bash
# Connect to Postgres (default user is your macOS user)
psql postgres

# In psql:
CREATE USER sellscope WITH PASSWORD 'sellscope_dev_password';
CREATE DATABASE sellscope OWNER sellscope;
\q
```

If you use a different user/password, remember them for the next step.

### 2. Configure the API

```bash
cd apps/api
cp .env.example .env
```

Edit `.env` and set:

```env
DATABASE_URL=postgresql+asyncpg://sellscope:sellscope_dev_password@localhost:5432/sellscope
REDIS_URL=redis://localhost:6379/0
DEBUG=true
```

(Use the same user/password/database you created in step 1.)

### 3. Install API dependencies and run the API

```bash
cd apps/api
pip3 install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Leave this running. Tables are created on first request (init_db runs at startup).

### 4. Run the frontend

In a **new terminal**:

```bash
cd apps/web
pnpm install
pnpm dev
```

Open http://localhost:3000. The app talks to the API at http://localhost:8000.

If the frontend is configured to proxy to the API, set in `apps/web/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

(Or use the Next.js rewrite that proxies `/api/v1/*` to the API; then you don’t need this if the frontend uses `/api/v1` as base URL.)

### 5. Load data into the API

Either import a JSON you already scraped:

```bash
cd scraper
python3 import_json_to_api.py output/adobe_stock_fruit_*.json
```

Or scrape and sync in one go (with API running):

```bash
cd scraper
export API_BASE_URL=http://localhost:8000
python3 api_integration.py "fruit" -n 10 --details --similar
```

Then in the app: **Dashboard → Scraped Assets** and **Dashboard → Insights**.

---

## Quick reference

| What you want to test | Need Docker? | What to run |
|------------------------|-------------|-------------|
| Scraper + CSV/JSON     | No          | `scraper`: `python3 adobe_stock_scraper.py "fruit" -n 10 --headless` |
| API + DB + frontend    | No (use local Postgres + Redis) | Start Postgres & Redis → `apps/api`: uvicorn → `apps/web`: pnpm dev |
| API + DB + frontend    | Yes         | `docker-compose -f docker-compose.dev.yml up -d` then run API + web as above |
