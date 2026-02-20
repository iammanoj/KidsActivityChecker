# Kids Activity Tracker

AI-powered agentic workflow that recommends kid-friendly activities based on weather, location, ratings, and cost — built for a family with two girls (ages 8 and 14).

## How It Works

```
Detect Location → Check Weather → Search Events → AI Ranking → Categorize → Evaluate
```

1. **Weather Check** — Fetches real-time weather (OpenWeatherMap + Open-Meteo fallback). If ≥65°F and no rain → outdoor mode, otherwise → indoor mode.
2. **Event Search** — Searches for free and paid activities within 15 miles using Tavily, across 3 age groups (family, age 8, age 14).
3. **AI Ranking** — GPT-4o parses raw search results into structured events and ranks them by cost, rating, age-fit, girl-friendly appeal, social value, and distance.
4. **Categorization** — Groups activities into 6 categories (Educational, Sports, Arts, Social, Nature, Entertainment), top 5 per category.
5. **Evaluation** — Runs 3 eval types to measure recommendation quality.

## Eval System

| Type | What It Does |
|------|-------------|
| **Code-based** (9 checks) | Deterministic: radius compliance, rating threshold, cost ordering, category validity, age labeling, weather consistency, duplicates, keyword relevance |
| **LLM Judge** (GPT-4o) | Scores output on relevance, age-appropriateness, diversity, and description quality (1-5 each) |
| **Human Feedback** | Thumbs up/down on each activity card, stored in SQLite |

## Tech Stack

- **Python 3.11+** with LangChain + LangGraph
- **GPT-4o** for ranking and LLM judge evals
- **Tavily** for web search
- **OpenWeatherMap / Open-Meteo** for weather
- **Streamlit** for UI
- **SQLite** for persistence

## Quick Start

```bash
# 1. Clone
git clone https://github.com/iammanoj/KidsActivityChecker.git
cd KidsActivityChecker

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up API keys
cp .env.example .env
# Edit .env with your keys:
#   OPENAI_API_KEY=sk-...
#   TAVILY_API_KEY=tvly-...
#   OPENWEATHERMAP_API_KEY=...  (optional, falls back to Open-Meteo)
#   ANTHROPIC_API_KEY=sk-ant-... (optional, not used in current MVP)

# 5. Run the app
streamlit run app.py

# 6. Run tests
python -m pytest tests/ -v
```

## Project Structure

```
KidsActivityChecker/
├── app.py                  # Streamlit entry point
├── agent/
│   ├── graph.py            # LangGraph workflow
│   ├── state.py            # State schema and constants
│   ├── nodes/              # Pipeline nodes (location, weather, search, rank, categorize)
│   └── tools/              # API wrappers (weather, Tavily search)
├── evals/
│   ├── code_evals.py       # 9 deterministic eval checks
│   ├── llm_judge.py        # GPT-4o judge with 4-criteria rubric
│   ├── rubric.py           # Judge prompt definitions
│   └── run_evals.py        # Eval orchestrator
├── db/                     # SQLite schema and operations
├── ui/                     # Streamlit components and dashboard
└── tests/                  # 84 tests covering all modules
```

## Ranking Criteria

Activities are scored using weighted multi-criteria ranking:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Cost | 25% | Free events prioritized |
| Rating | 20% | Minimum 3.5/5 stars |
| Age-appropriateness | 20% | Suitable for ages 8 and/or 14 |
| Girl-friendly appeal | 15% | Activities appealing to girls |
| Social/collaborative | 10% | Team activities, meeting other kids |
| Distance | 10% | Closer is better (15-mile max) |

## API Keys

| Service | Required | Free Tier |
|---------|----------|-----------|
| OpenAI | Yes | Pay-per-use |
| Tavily | Yes | 1000 searches/month |
| OpenWeatherMap | No | Falls back to Open-Meteo (free, no key) |
| Anthropic | No | Not used in current MVP |

## License

MIT
