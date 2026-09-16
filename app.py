from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from math import radians, sin, cos, asin, sqrt
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from db import listings_col, buyers_col, orders_col, seed_buyers_if_empty, get_buyers_for_crop
import ai_assistant

app = FastAPI(title="AgriNexus API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await seed_buyers_if_empty()


# ---------- helpers ----------

def km(a, b, c, d):
    R = 6371
    dlat = radians(c - a)
    dlng = radians(d - b)
    h = sin(dlat / 2) ** 2 + cos(radians(a)) * cos(radians(c)) * sin(dlng / 2) ** 2
    return 2 * R * asin(sqrt(h))


def oid_str(doc):
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ---------- models ----------

class Listing(BaseModel):
    crop: str
    quantity: float
    asking_price: float
    lat: float = 17.54
    lng: float = 78.49
    days_to_harvest: int = 2
    farmer_name: Optional[str] = None


class Buyer(BaseModel):
    name: str
    crop: str
    qty: float
    price: float
    lat: float
    lng: float


class AssistantExplainRequest(BaseModel):
    crop: str
    analysis: dict
    language: str = "en"  # "en" | "hi" | "te"


class ChatMessage(BaseModel):
    role: str
    content: str


class AssistantChatRequest(BaseModel):
    messages: List[ChatMessage]
    language: str = "en"


# ---------- health ----------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------- listings (MongoDB) ----------

@app.post("/listings")
async def create_listing(x: Listing):
    doc = x.dict()
    doc["created_at"] = datetime.utcnow()
    result = await listings_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@app.get("/listings")
async def list_listings():
    cursor = listings_col.find().sort("created_at", -1)
    return [oid_str(d) async for d in cursor]


# ---------- buyers (MongoDB) ----------

@app.post("/buyers")
async def add_buyer(b: Buyer):
    doc = b.dict()
    result = await buyers_col.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


@app.get("/buyers")
async def list_buyers():
    cursor = buyers_col.find()
    return [oid_str(d) async for d in cursor]


# ---------- core matching / analysis ----------

@app.post("/analyze")
async def analyze(x: Listing):
    crop = x.crop.strip()
    buyers = await get_buyers_for_crop(crop)

    candidates = []
    for b in buyers:
        dist = round(km(x.lat, x.lng, b["lat"], b["lng"]), 1)
        score = round(max(0, 100 - dist * 2) + min(30, b["price"] - x.asking_price), 1)
        candidates.append({**oid_str(b), "distance_km": dist, "match_score": score})
    candidates.sort(key=lambda z: z["match_score"], reverse=True)

    remaining = x.quantity
    matches = []
    revenue = 0
    for b in candidates:
        if remaining <= 0:
            break
        q = min(remaining, b["qty"])
        remaining -= q
        revenue += q * b["price"]
        matches.append({"buyer": b["name"], "quantity": q, "price": b["price"], "distance_km": b["distance_km"]})

    avg = round(revenue / (x.quantity - remaining), 2) if x.quantity > remaining else x.asking_price
    demand = "High" if sum(b["qty"] for b in candidates) >= x.quantity else ("Medium" if candidates else "Low")
    suggested = round(max(x.asking_price, avg - 1), 2) if candidates else x.asking_price
    traditional_consumer = round(suggested * 1.35, 2)
    direct_consumer = round(suggested * 1.12, 2)

    result = {
        "demand": demand,
        "suggested_price": suggested,
        "matched_quantity": x.quantity - remaining,
        "unmatched_quantity": remaining,
        "estimated_revenue": round(revenue, 2),
        "matches": matches,
        "traditional_estimated_consumer_price": traditional_consumer,
        "agrinexus_estimated_consumer_price": direct_consumer,
        "buyer_saving_pct": round((traditional_consumer - direct_consumer) / traditional_consumer * 100, 1) if traditional_consumer else 0,
        "explanation": f"{demand} nearby demand detected for {x.crop}. Suggested price is \u20b9{suggested}/kg based on matching buyer offers. Prioritize nearby buyers and aggregate deliveries to reduce transport cost.",
    }

    # persist the order/analysis for later aggregation
    order_doc = {
        "listing": x.dict(),
        "result": result,
        "created_at": datetime.utcnow(),
    }
    inserted = await orders_col.insert_one(order_doc)
    result["order_id"] = str(inserted.inserted_id)

    return result


@app.get("/orders")
async def list_orders():
    cursor = orders_col.find().sort("created_at", -1)
    return [oid_str(d) async for d in cursor]


# ---------- OpenRouter-powered multilingual assistant ----------

@app.post("/assistant/explain")
async def assistant_explain(req: AssistantExplainRequest):
    text = await ai_assistant.explain_analysis(req.crop, req.analysis, req.language)
    return {"explanation": text, "language": req.language}


@app.post("/assistant/chat")
async def assistant_chat(req: AssistantChatRequest):
    messages = [m.dict() for m in req.messages]
    text = await ai_assistant.chat(messages, req.language)
    return {"reply": text, "language": req.language}
