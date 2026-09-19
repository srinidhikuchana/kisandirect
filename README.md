# AgriNexus — SIH26033

A working React + FastAPI marketplace prototype for direct farmer/FPO-to-buyer trade, with MongoDB support, OR-Tools pickup/delivery planning, order aggregation, demand forecasting, and optional OpenRouter and OpenWeather integrations.

## Start in 5 minutes (no API keys required)

Install Python 3.11+ and Node.js 20.19+ or 22.12+. Open two terminals in the extracted `agrinexus` directory.

**Terminal 1 — API**

```sh
cd backend
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
```

macOS/Linux:
```sh
source .venv/bin/activate
cp .env.example .env
```

Then on either system:
```sh
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Terminal 2 — React**

```sh
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Backend API documentation: http://localhost:8000/docs.

Choose Farmer, Buyer, or FPO/Admin under “Explore the local demo.” These are shared sample personas with fictional listings. Browser reload signs you out; orders and listings persist in the backend. No payment is collected, and no courier is booked.

Default storage is a local JSON file so the app works immediately. This is explicitly a single-process local demo; run only one backend process. It is not MongoDB until configured below.

## Switch to MongoDB

Use a local MongoDB server or an Atlas Free cluster. In `backend/.env`:

```dotenv
STORAGE=mongodb
MONGODB_URI=mongodb+srv://USERNAME:PASSWORD@YOUR_CLUSTER/agrinexus
MONGODB_DB=agrinexus
```

Use the URI from your own Atlas account. URL-encode special characters in database passwords. Add only required client/backend IP addresses to Atlas's network access list. Restart the backend. MongoDB receives a fresh set of seed data if demo mode is on. JSON data is not automatically migrated.

**Database design:** This bounded prototype stores users, listings, and orders in one versioned MongoDB document. Optimistic compare-and-swap ensures stock reservation and order creation/cancellation commit together, including across backend workers. This is intentionally simple, not a production schema: MongoDB's 16 MiB document limit applies, and contention grows with usage. A real rollout should split users/listings/orders into indexed collections and use transactions. Do not represent this prototype as production-ready.

## Optional APIs (backend only)

Never put API keys, MongoDB credentials, or JWT signing secrets in React, VITE variables, screenshots, or Git.

OpenRouter:
```dotenv
OPENROUTER_API_KEY=your-key
OPENROUTER_MODEL=openrouter/free
```
The server only permits `openrouter/free` or models ending in `:free`. Free-model availability and quotas vary. Missing keys show clearly labelled built-in help in English, Telugu or Hindi, not simulated AI. Provider errors appear visibly without blocking marketplace functionality. Multilingual replies do not mean the entire interface is translated.

OpenWeather:
```dotenv
OPENWEATHER_API_KEY=your-key
```
Uses `/data/2.5/weather` for current conditions at the default Medchal location. Missing keys show an unavailable message, never invented weather. Choose a plan covering this endpoint; do not accidentally enrol in a paid One Call plan. API entitlement must be verified in your own account.

## A complete demo walkthrough

1. Sign in as Farmer and add a harvest listing. Supply the farm's coordinates.
2. Sign out, enter Buyer, and place two orders with delivery coordinates and the same date.
3. Sign in as FPO/Admin. Open Overview → Group orders to aggregate demand by crop/date.
4. In Orders, accept those orders.
5. Open Logistics, choose their delivery date, vehicle count, capacity and depot. Plan deliveries.
6. The map shows ordered pickups and drop-offs. Capacity is enforced; pickup occurs before delivery on the same vehicle.
7. In Orders, dispatch and then mark delivered. A buyer can cancel placed/accepted orders; stock is returned once.
8. Open Insights. Sparse data is labelled insufficient. No fake forecast or claimed accuracy is supplied.
9. Ask the Assistant in English, Telugu or Hindi. Without a key, it provides predefined help.

## What is implemented

| Area | Behaviour |
|---|---|
| Accounts | Farmer/buyer signup; scrypt password hashing; expiring signed tokens; server-side role checks; admin provisioned via CLI |
| Farmer | Add crop, kg, price, harvest date and pickup location; view own orders |
| Buyer | Search produce; place orders; view/cancel own orders; match growers |
| Matching | Ranks in-stock listings by produce cost plus an illustrative distance weight; not ML or a delivery quote |
| FPO/Admin | View network orders, aggregate crop/date demand, accept/dispatch/deliver, plan routes |
| Inventory | Atomic reservation with order creation; atomic stock return on cancellation; rejects overselling |
| Demand forecast | Ridge regression with trend and weekly seasonality; last seven days held out for MAE; requires 14 distinct order days |
| Price prediction | Ridge regression on daily volume-weighted transaction prices; next-day estimate with holdout MAE |
| Logistics | OR-Tools multi-vehicle pickup/delivery, capacity limits, depot return; up to 40 accepted orders per run |
| Map | Leaflet + attributed OpenStreetMap tiles; dashed straight-line segments, not road routing |
| AI | Optional OpenRouter free model; English/Telugu/Hindi answers; no action-execution privileges |
| Weather | Optional live OpenWeather current conditions |

The demand forecast uses aggregated marketplace orders, including accepted/placed/delivered and excluding cancellations. It measures recorded orders, not all potential demand: stockouts and cancellations can bias it. Days without orders are zero-filled. The prediction and holdout error are baselines, not validated agricultural advice. Price prediction uses a separate Ridge model fitted to daily volume-weighted transaction prices and reports a held-out error. There is no external mandi-price data integration; neither model has been validated for real-world deployment.

Route distances use geographic straight-line distance, not driving time. The optimiser proposes a feasible plan within a short search budget; it does not prove a global optimum. No time windows, road closures, refrigeration, driver assignment, or real-time tracking are implemented. Integrate a properly licensed road-distance matrix before claiming road-route savings. Route plans are calculated on demand and not persisted or dispatched.

## Free stack and limits

React, FastAPI, scikit-learn, OR-Tools and Leaflet can run locally without paid API subscriptions. Local MongoDB is an option; hosted free tiers have limits. An API key is a credential, not a guarantee of free usage. No paid service is required for the core local demo.

Official references checked 19 September 2026:
- MongoDB Atlas Free cluster limits: https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/ (0.5 GB storage; other limits apply).
- OpenRouter quota/credit rules: https://openrouter.ai/docs/api-reference/limits
- OpenWeather plans: https://openweathermap.org/price
- Render free-service behaviour: https://render.com/docs/free
- OpenStreetMap tile usage policy: https://operations.osmfoundation.org/policies/tiles/ — attribution, caching and service rules apply; no bulk/offline downloading. Public tiles have no SLA. Use a compliant provider or self-host for scaled usage.

These services' terms and quotas can change. The project does not create accounts, activate billing, or provision hosting. Streamlit is not necessary: React is the frontend and FastAPI runs Python/ML.

## Hosting when your team is ready

Build the frontend with `npm run build`; deploy its `dist` directory to a static host. Before building, set `VITE_API_URL` to the HTTPS backend URL. This public setting must contain only the backend origin.

A Python host must run `uvicorn main:app --host 0.0.0.0 --port $PORT` from `backend` after installing requirements. Set `STORAGE=mongodb`, Atlas credentials and exact frontend origins in `CORS_ORIGINS`. Use HTTPS. Free hosts may sleep or have memory/build quotas; OR-Tools/scikit-learn may exceed some tiny plans. The local demo is the reliable zero-subscription fallback.

Before any public test:
1. Start with a fresh empty database and set `DEMO_MODE=false` to disable public demo personas (especially the admin persona). A database previously seeded in demo mode retains those users; use a fresh database.
2. Generate and set a strong persistent `JWT_SECRET` (e.g. `python -c "import secrets; print(secrets.token_hex(32))"`). Restart the server.
3. Run `python create_admin.py` with the backend stopped to provision your own FPO/admin account.
4. Add rate limiting for login, signup, AI, weather and route calculation at a reverse proxy or application layer. This prototype does not include deployment-grade abuse prevention.
5. Add monitoring, backups, email verification, password recovery, account review, data retention controls and privacy notices before accepting real personal information. Validate inventory and fulfilment policies with farmers.

No public deployment or paid account has been created. Public production readiness, payments, disputes, farmer verification, file uploads and driver integrations are outside this prototype.

## Verify

```sh
cd backend
pytest -q
```

The integration test covers role isolation, insufficient stock, stock reservation/restoration, duplicate cancellation rejection, transitions, order aggregation, a feasible pickup/delivery route, and infeasible capacity. It uses a temporary JSON store, not your data. MongoDB and optional providers need separate integration checks with your credentials.

Frontend build:
```sh
cd frontend
npm run build
```
