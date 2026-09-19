# MongoDB setup

## MongoDB Atlas
1. Create a free MongoDB Atlas cluster.
2. Create a database user.
3. Allow your development/deployment IP in Network Access (for a hackathon demo, use the Atlas option appropriate to your security requirements).
4. Copy the Python driver connection string.
5. Put it in `backend/.env` as `MONGODB_URI=...`.
6. Set `MONGODB_DB=agrinexus`.
7. Start FastAPI and open `/seed` once, or run the seed request from Swagger at `/docs`.

Collections used by the prototype:
- `listings` — farmer produce listings
- `orders` — buyer orders

Future collections:
- `users`
- `buyers`
- `fpos`
- `delivery_routes`
- `market_prices`
- `ai_interactions`
