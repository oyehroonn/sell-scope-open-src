# SellScope

**The Bloomberg Terminal for Stock Contributors**

An open-source intelligence platform that transforms stock contribution from guesswork into data-driven creation. Get opportunity scoring, AI briefs, portfolio coaching, and automated workflows — all in one platform.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-alpha-orange.svg)

## Features

### Core Intelligence

- **Opportunity Scoring** - Every keyword gets a 0-100 score based on demand, competition, seasonality, and production difficulty
- **Visual Whitespace Analysis** - AI-powered detection of visual gaps in any niche
- **AI Brief Generator** - Turn opportunities into production briefs with shot ideas, keywords, and AI prompts
- **Portfolio Coach** - Identify underperformers, cannibalization, and expansion opportunities

### Automation

- **Custom Playwright Scraper** - Reliable data collection from Adobe Stock
- **Make.com Integration** - Webhooks for social media automation and workflows
- **Chrome Extension** - In-portal assistance and real-time opportunity overlays

### Analytics

- **Trending Keywords** - Real-time market pulse
- **Seasonal Calendar** - Event-based planning with upload deadlines
- **Benchmark Network** - Anonymous aggregated contributor data (opt-in)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 + TypeScript + Tailwind + shadcn/ui |
| Backend | Python FastAPI |
| Scraping | Playwright |
| Database | PostgreSQL + pgvector |
| Cache/Queue | Redis + Celery |
| AI | CLIP/SigLIP + BLIP-2 (local) or Gemini/GPT-4o (cloud) |

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 16+ with pgvector
- Redis

### Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/sellscope/sellscope.git
cd sellscope
```

2. **Install dependencies**

```bash
# Install pnpm if you haven't
npm install -g pnpm

# Install all dependencies
pnpm install
```

3. **Set up environment variables**

```bash
# Frontend
cp apps/web/.env.example apps/web/.env.local

# Backend
cp apps/api/.env.example apps/api/.env
```

4. **Start the database**

```bash
docker compose up db redis -d
```

5. **Run the backend**

```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --reload
```

6. **Run the frontend**

```bash
pnpm dev
```

7. **Open the app**

Visit [http://localhost:3000](http://localhost:3000)

### Docker (Full Stack)

```bash
docker compose up
```

This starts:
- PostgreSQL with pgvector on port 5432
- Redis on port 6379
- FastAPI backend on port 8000
- Next.js frontend on port 3000

## Project Structure

```
sellscope/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── app/               # App router pages
│   │   ├── components/        # React components
│   │   └── lib/               # Utilities
│   └── api/                    # FastAPI backend
│       ├── app/
│       │   ├── routers/       # API endpoints
│       │   ├── services/      # Business logic
│       │   └── models/        # Database models
│       └── main.py            # Entry point
├── extensions/
│   └── chrome/                 # Browser extension
├── packages/                   # Shared packages (future)
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Keywords

- `GET /keywords/search` - Search keywords with opportunity data
- `GET /keywords/trending` - Get trending keywords
- `GET /keywords/suggestions` - Autocomplete suggestions

### Opportunities

- `GET /opportunities/score/{keyword}` - Get opportunity score
- `POST /opportunities/analyze` - Trigger full analysis
- `GET /opportunities/top` - Get top opportunities
- `GET /opportunities/heatmap` - Category heatmap

### Portfolios

- `GET /portfolios/my` - Get user's portfolios
- `POST /portfolios/track` - Track a competitor
- `GET /portfolios/{id}/coach` - Get coaching insights

### Briefs

- `POST /briefs/generate` - Generate production brief
- `POST /briefs/keywords` - Generate keyword strategies
- `POST /briefs/prompts` - Generate AI prompts

### Webhooks

- `POST /webhooks` - Create webhook
- `GET /webhooks` - List webhooks
- `POST /webhooks/incoming/make` - Make.com receiver

## Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extensions/chrome` folder

The extension provides:
- Real-time opportunity scores on search results
- Keyword suggestions while uploading
- Quick access to briefs and analysis

## Self-Hosting vs Hosted

### Self-Hosted (Free)

- Full functionality
- Bring your own infrastructure
- No benchmark network access
- Manual scraper setup

### Hosted (Coming Soon)

| Tier | Price | Includes |
|------|-------|----------|
| Starter | $5/mo | 1000 keyword lookups, 50 portfolio analyses |
| Pro | $15/mo | Unlimited lookups, benchmark access, Make.com |
| Agency | $49/mo | Multi-account, API access, white-label |

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- Adobe Stock for the platform we're building tools for
- The open-source community for the amazing tools we use
- All contributors who help make this project better

---

**SellScope** - Stop guessing, start selling.
