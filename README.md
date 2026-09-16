# AgriNexus SIH26033 — MongoDB + OpenRouter Prototype

Implements the Kisan-Direct flow: produce listing, demand analysis, price
recommendation, buyer matching, order aggregation — now backed by MongoDB,
with an OpenRouter-powered multilingual (Telugu/Hindi/English) AI assistant.

## What changed from the demo build
- **MongoDB (via Motor, async driver)** replaces the hardcoded in-memory buyer
  list. Buyers, listings, and every analyzed order are persisted.
- **OpenRouter integration** (`ai_assistant.py`) powers two things:
  1. A natural-language explanation of each analysis result, in the farmer's
     chosen language.
  2. A free-form chat assistant widget on the page.
- The API key is read from an environment variable — never hardcoded or sent
  to the browser. The frontend only ever talks to your own FastAPI backend.

## Setup

1. **Get a MongoDB connection string.**
   Easiest option: free-tier cluster on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
   Or run MongoDB locally (`mongodb://localhost:27017` needs nothing else set).

2. **Get an OpenRouter API key.**
   Sign up at [openrouter.ai](https://openrouter.ai/keys) and create a key.
   This project defaults to `openai/gpt-4o-mini`, which is paid but cheap
   (~$0.15 per 1M input tokens) — add a few dollars of credit at
   [openrouter.ai/credits](https://openrouter.ai/credits). If you'd rather
   not spend anything, swap `OPENROUTER_MODEL` in `.env` for a free model
   like `meta-llama/llama-3.3-70b-instruct:free`.

3. **Configure environment variables.**
   ```
   cp .env.example .env
   ```
   Fill in `MONGODB_URI` and `OPENROUTER_API_KEY` in `.env`.

4. **Install and run the backend.**
   ```
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app:app --reload --port 8000
   ```
   On startup, if the `buyers` collection is empty it's auto-seeded with the
   same demo buyers as before, so you can test immediately.

5. **Serve the frontend.**
   ```
   python -m http.server 5500
   ```
   Open `http://localhost:5500`.

## API endpoints

| Method | Path                 | Purpose                                             |
|--------|----------------------|------------------------------------------------------|
| GET    | /health              | Liveness check                                       |
| POST   | /listings            | Save a farmer's produce listing to MongoDB            |
| GET    | /listings            | List saved listings                                   |
| POST   | /buyers              | Add a buyer to MongoDB                                |
| GET    | /buyers              | List buyers                                           |
| POST   | /analyze             | Match a listing against buyers, persist as an order   |
| GET    | /orders              | List past analyzed orders                             |
| POST   | /assistant/explain   | OpenRouter explanation of an analysis, in en/hi/te    |
| POST   | /assistant/chat      | Free-form multilingual chat with the assistant        |

`language` accepts `"en"`, `"hi"`, or `"te"`.

## Notes
- If `OPENROUTER_API_KEY` is missing, `/assistant/*` still respond — they
  fall back to the plain demo explanation instead of erroring out, so the
  rest of the app keeps working while you're setting things up.
- Price/demand numbers are still demo calculations based on the seeded buyer
  data, not live market prices.

## Still on the roadmap (not in this build)
- Firebase Authentication for farmer/buyer/admin roles
- OR-Tools for multi-stop delivery route optimization
- Leaflet + OpenStreetMap map view
- Admin/FPO dashboard views
