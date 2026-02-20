# Kids Activity Tracker - Product Requirements Document (PRD)

**Version:** 1.0 (MVP)
**Date:** 2025-02-19
**Author:** Manoj Mohan
**Status:** Draft - Pending Approval

---

## 1. Overview

### 1.1 Problem Statement
Parents of school-age children need a quick, reliable way to discover age-appropriate, highly-rated activities and events near them — tailored to current weather, budget constraints, and their children's interests. Manual searching across multiple sites is time-consuming and often yields irrelevant results.

### 1.2 Solution
An AI-powered agentic workflow that automatically checks the weather, determines indoor/outdoor suitability, searches for local events within a 15-mile radius, and returns a prioritized, categorized list of activities — optimized for two girls (ages 8 and 14).

### 1.3 Target User
- Primary user: Parent (Manoj) running the app for family activity planning
- Beneficiaries: Two daughters, ages 8 and 14

---

## 2. Core Features (MVP)

### 2.1 Weather-Based Decision Engine

| Attribute | Detail |
|-----------|--------|
| **Default location** | Los Altos, California |
| **Location detection** | Auto-detect via IP geolocation with manual override option |
| **Weather API** | OpenWeatherMap (free tier) |
| **Outdoor threshold** | Temperature >= 65°F AND no rain/snow |
| **Indoor trigger** | Temperature < 65°F OR rain/snow/severe weather |
| **Data points used** | Temperature, precipitation, wind speed, weather condition code |

**Behavior:**
- On app load, detect location via IP (fallback to Los Altos, CA)
- Fetch current weather + forecast for today and upcoming weekend
- Classify as OUTDOOR or INDOOR mode
- Display weather summary card in UI

### 2.2 Event Discovery Engine

| Attribute | Detail |
|-----------|--------|
| **Search API** | Tavily Search API |
| **Search radius** | 15 miles from detected/configured location |
| **Time modes** | Today (current day) and Weekend (upcoming Sat/Sun) |
| **LLM for agent** | Claude (Anthropic API) via LangChain |

**Search Strategy:**
1. Construct targeted search queries based on weather mode (indoor/outdoor)
2. Include location, radius, date, and age-appropriate keywords
3. Search for free events first, then paid events as fallback
4. Extract structured data: name, location, cost, rating, description, URL, category

### 2.3 Multi-Criteria Ranking System

Activities are scored and ranked using the following weighted criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Cost** | 25% | Free events score highest. Paid events scored inversely by price. |
| **Rating** | 20% | Minimum 3.5/5 stars to be included. Higher = better score. |
| **Age appropriateness** | 20% | Must be suitable for target age group (8 and/or 14). |
| **Girl-friendly appeal** | 15% | Prioritize activities that are appealing/enticing to girls. |
| **Social/collaborative** | 10% | Team-building, group activities, opportunities to meet other kids. |
| **Distance** | 10% | Closer events score higher within the 15-mile radius. |

**Hard Filters (must pass all):**
- Within 15-mile radius
- Rating >= 3.5/5 (when rating data is available)
- Age-appropriate for at least one child (8 or 14)

### 2.4 Age-Based Recommendation Modes

The app produces three recommendation sets per run:

| Mode | Target | Description |
|------|--------|-------------|
| **Joint** | Both kids (8 & 14) | Activities enjoyable for both age groups together |
| **Younger** | 8-year-old | Age-appropriate activities for elementary-age child |
| **Older** | 14-year-old | Age-appropriate activities for teen |

### 2.5 Activity Categories

Results are categorized into:

| Category | Examples |
|----------|----------|
| **Educational** | Museum exhibits, science workshops, library programs |
| **Sports & Fitness** | Soccer clinics, swim lessons, hiking, biking trails |
| **Arts & Crafts** | Painting classes, pottery, DIY workshops |
| **Social & Community** | Community events, volunteer opportunities, group meetups |
| **Nature & Outdoor** | Parks, botanical gardens, nature walks, farmers markets |
| **Entertainment** | Movies, shows, festivals, arcades, escape rooms |

Each category shows up to **5 activities** (sorted by ranking score).

### 2.6 Output Structure

Each activity recommendation includes:

```
- Activity Name
- Category (Educational / Sports / Arts / Social / Nature / Entertainment)
- Location (name + address)
- Distance from user (miles)
- Cost (Free / $X.XX)
- Rating (X.X/5 stars, source)
- Age suitability (Joint / 8yr / 14yr / Both)
- Why recommended (1-2 sentence LLM-generated explanation)
- URL/link (when available)
```

---

## 3. Eval System

### 3.1 Overview

Three evaluation types are implemented to measure and improve the agent's output quality:

| Eval Type | Purpose | Automated? |
|-----------|---------|------------|
| **Code-based** | Deterministic structural/constraint checks | Yes |
| **LLM-judge** | Quality scoring via multi-criteria rubric | Yes |
| **Human-in-the-loop** | User feedback on recommendations | Manual |

### 3.2 Code-Based Evals

Deterministic checks that run automatically on every agent output:

| Check | Rule | Pass/Fail |
|-------|------|-----------|
| **Result count** | Each category has 0-5 results | Pass if within bounds |
| **Radius compliance** | All events within 15-mile radius | Pass if all comply |
| **Cost ordering** | Free events listed before paid events | Pass if ordered correctly |
| **Rating threshold** | No event below 3.5 stars (when rated) | Pass if all >= 3.5 |
| **Category validity** | All events assigned to valid categories | Pass if categories match enum |
| **Age labeling** | Every event has age suitability tag | Pass if all tagged |
| **Weather consistency** | Indoor/outdoor mode matches weather data | Pass if consistent |
| **Keyword relevance** | Activity descriptions contain age-appropriate keywords | Pass if relevance score > threshold |
| **No duplicates** | No duplicate events across categories | Pass if all unique |

### 3.3 LLM-Judge Evals

An OpenAI GPT-4o judge scores the agent's output on a multi-criteria rubric:

| Criterion | Score Range | Description |
|-----------|-------------|-------------|
| **Relevance** | 1-5 | Are activities relevant to the weather, location, and time? |
| **Age-appropriateness** | 1-5 | Are activities suitable for the target age groups (8 & 14)? |
| **Diversity** | 1-5 | Is there a good variety across categories and activity types? |
| **Description quality** | 1-5 | Are the "why recommended" explanations helpful and specific? |

- **Overall score** = average of all criteria
- **Pass threshold** = overall score >= 3.5/5
- Judge uses a fixed rubric prompt with examples of good/bad outputs
- Agent LLM (Claude) and judge LLM (OpenAI) are intentionally different to avoid self-grading bias

### 3.4 Human-in-the-Loop Eval

- Each activity card in the Streamlit UI has a **thumbs up / thumbs down** button
- Feedback is stored in SQLite with: activity_id, timestamp, vote (up/down), session_id
- Dashboard shows aggregated feedback stats over time
- Enables tracking of which types of recommendations users actually find helpful

---

## 4. Technical Architecture

### 4.1 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.11+ |
| **Agent framework** | LangChain (with LangGraph for workflow orchestration) |
| **Agent LLM** | Claude (Anthropic API) |
| **Eval judge LLM** | OpenAI GPT-4o |
| **Web search** | Tavily Search API |
| **Weather API** | OpenWeatherMap API (free tier) |
| **IP geolocation** | ip-api.com (free, no key required) |
| **UI** | Streamlit |
| **Database** | SQLite (local persistence) |
| **Package management** | pip with requirements.txt |

### 4.2 Agent Workflow (LangGraph)

```
[Start]
   |
   v
[1. Detect Location] --> IP geolocation (or manual override)
   |
   v
[2. Check Weather] --> OpenWeatherMap API
   |
   v
[3. Decide Mode] --> OUTDOOR (>=65°F, no rain) or INDOOR
   |
   v
[4. Search Events] --> Tavily search with targeted queries
   |                    (3 queries: joint, age-8, age-14)
   v
[5. Parse & Filter] --> Extract structured data, apply hard filters
   |
   v
[6. Rank & Score] --> Apply weighted multi-criteria ranking
   |
   v
[7. Categorize] --> Assign to 6 categories, top 5 per category
   |
   v
[8. Generate Explanations] --> LLM writes "why recommended" for each
   |
   v
[9. Run Code Evals] --> Deterministic checks on output
   |
   v
[10. Run LLM Judge] --> GPT-4o scores output quality
   |
   v
[11. Store Results] --> Save to SQLite
   |
   v
[12. Return to UI] --> Display in Streamlit dashboard
```

### 4.3 Project Structure

```
KidsActivityChecker/
├── app.py                     # Streamlit entry point
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── PRD.md                     # This document
│
├── agent/
│   ├── __init__.py
│   ├── graph.py               # LangGraph workflow definition
│   ├── state.py               # Agent state schema
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── location.py        # IP geolocation node
│   │   ├── weather.py         # Weather check node
│   │   ├── search.py          # Tavily event search node
│   │   ├── rank.py            # Multi-criteria ranking node
│   │   └── explain.py         # LLM explanation generation node
│   └── tools/
│       ├── __init__.py
│       ├── weather_tool.py    # OpenWeatherMap wrapper
│       └── search_tool.py     # Tavily search wrapper
│
├── evals/
│   ├── __init__.py
│   ├── code_evals.py          # Deterministic code-based evals
│   ├── llm_judge.py           # LLM-as-judge eval (OpenAI GPT-4o)
│   ├── rubric.py              # Judge rubric/prompt definitions
│   └── run_evals.py           # Eval runner and reporting
│
├── db/
│   ├── __init__.py
│   ├── models.py              # SQLite schema / ORM models
│   └── database.py            # DB connection and operations
│
├── ui/
│   ├── __init__.py
│   ├── components.py          # Reusable Streamlit components
│   ├── dashboard.py           # Main dashboard layout
│   └── eval_view.py           # Eval results display
│
└── tests/
    ├── test_code_evals.py     # Tests for code-based eval functions
    ├── test_ranking.py        # Tests for ranking logic
    └── test_weather.py        # Tests for weather decision logic
```

### 4.4 Data Models

**AgentState (LangGraph state):**
```python
class AgentState(TypedDict):
    location: dict          # {city, state, lat, lon}
    weather: dict           # {temp_f, condition, is_outdoor}
    mode: str               # "indoor" | "outdoor"
    time_mode: str          # "today" | "weekend"
    raw_search_results: list
    filtered_events: list
    ranked_events: list
    categorized_output: dict
    eval_results: dict
```

**Event Schema:**
```python
@dataclass
class Event:
    name: str
    category: str           # enum of 6 categories
    location_name: str
    address: str
    distance_miles: float
    cost: float             # 0.0 for free
    is_free: bool
    rating: float           # 0.0-5.0
    rating_source: str
    age_suitability: str    # "joint" | "younger" | "older" | "both"
    why_recommended: str
    url: str
    source_query: str
```

### 4.5 API Keys Required

| Service | Env Variable | Free Tier |
|---------|-------------|-----------|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | Pay-per-use |
| OpenAI (GPT-4o judge) | `OPENAI_API_KEY` | Pay-per-use |
| Tavily Search | `TAVILY_API_KEY` | 1000 free searches/month |
| OpenWeatherMap | `OPENWEATHERMAP_API_KEY` | 1000 free calls/day |

---

## 5. Streamlit UI Layout

### 5.1 Dashboard Layout

```
┌──────────────────────────────────────────────────────┐
│  SIDEBAR                │  MAIN CONTENT AREA         │
│                         │                             │
│  📍 Location            │  ☀️ Weather Summary Card    │
│  [Auto-detected]        │  [Temp | Condition | Mode]  │
│  [Override input]       │                             │
│                         │  ┌─ Tab: Today ──────────┐  │
│  📅 View Mode           │  │                       │  │
│  ○ Today                │  │  Category: Educational │  │
│  ○ Weekend              │  │  [Card] [Card] [Card]  │  │
│                         │  │                       │  │
│  👶 Age Filter          │  │  Category: Sports     │  │
│  ☑ Joint (both)         │  │  [Card] [Card]        │  │
│  ☑ Age 8                │  │                       │  │
│  ☑ Age 14               │  │  ... more categories   │  │
│                         │  └───────────────────────┘  │
│  💰 Cost Filter         │                             │
│  ○ Free only            │  ┌─ Tab: Weekend ────────┐  │
│  ○ All                  │  │  (same layout)        │  │
│                         │  └───────────────────────┘  │
│  📊 Eval Scores         │                             │
│  [Mini eval summary]    │  ┌─ Tab: Eval Results ───┐  │
│                         │  │  Code eval pass/fail   │  │
│  [🔄 Run Again]         │  │  LLM judge scores     │  │
│                         │  │  Human feedback stats  │  │
│                         │  └───────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 5.2 Activity Card

```
┌─────────────────────────────────────┐
│  🎨 Pottery Workshop for Kids       │
│  Arts & Crafts | ★ 4.5/5           │
│                                     │
│  📍 Community Art Center (2.3 mi)   │
│  💰 FREE                            │
│  👧 Joint (ages 8-14)              │
│                                     │
│  "Hands-on pottery class where kids │
│   collaborate in small groups..."   │
│                                     │
│  [🔗 Details]  [👍] [👎]           │
└─────────────────────────────────────┘
```

---

## 6. MVP Scope & Boundaries

### 6.1 In Scope (MVP)
- Weather-based indoor/outdoor decision engine
- Tavily-powered event search for Los Altos area (15-mile radius)
- Multi-criteria ranking with weighted scoring
- Three age modes: joint, younger (8), older (14)
- Six activity categories with top 5 per category
- All three eval types: code-based, LLM-judge, human feedback
- Streamlit dashboard with sidebar filters and tabbed results
- SQLite persistence for results and feedback
- Today + weekend time modes

### 6.2 Out of Scope (Post-MVP)
- User accounts / authentication
- Push notifications or scheduled runs
- Calendar integration (Google Calendar, Apple Calendar)
- Booking/RSVP directly through the app
- Social features (sharing activities with other parents)
- Mobile-native app (Streamlit is web-only)
- Multi-family support
- Real-time event API integrations (Eventbrite, Yelp, Google Places)
- Caching layer for repeated searches
- CI/CD pipeline
- Production deployment (runs locally for MVP)

---

## 7. Success Criteria

| Metric | Target |
|--------|--------|
| Code eval pass rate | >= 90% of checks pass per run |
| LLM judge overall score | >= 3.5/5 average |
| Human thumbs-up rate | >= 70% of rated activities |
| End-to-end latency | < 60 seconds per run |
| Activities returned | >= 10 total per run |

---

## 8. Assumptions

1. Tavily free tier (1000 searches/month) is sufficient for MVP usage
2. OpenWeatherMap free tier is sufficient for daily usage
3. User has Python 3.11+ installed locally
4. User has API keys for Anthropic, OpenAI, Tavily, and OpenWeatherMap
5. SQLite is adequate for MVP persistence (no concurrent users)
6. IP geolocation is accurate enough for city-level location detection
7. Web search results contain enough structured data (ratings, cost, location) for meaningful ranking

---

## 9. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tavily returns sparse/irrelevant results | Low quality recommendations | Craft multiple targeted queries; fallback to general activity suggestions |
| Rating data unavailable for most events | Ranking is less meaningful | Make rating weight lower when data missing; use LLM to estimate quality |
| Free events hard to find via search | Poor free-first experience | Maintain a curated list of known free venues (parks, libraries, trails) |
| IP geolocation inaccurate | Wrong area searched | Always show detected location; easy manual override |
| LLM hallucinations in event details | Incorrect recommendations | Code evals catch structural issues; LLM judge catches quality issues |
