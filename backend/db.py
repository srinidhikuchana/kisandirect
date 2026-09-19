import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB", "kisandirect")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

listings_col = db["listings"]
buyers_col = db["buyers"]
orders_col = db["orders"]

DEMO_BUYERS = [
    {"id": "B1", "name": "FreshMart Kompally", "crop": "Tomato", "qty": 180, "price": 34, "lat": 17.535, "lng": 78.486},
    {"id": "B2", "name": "Green Bowl Restaurant", "crop": "Tomato", "qty": 120, "price": 36, "lat": 17.505, "lng": 78.495},
    {"id": "B3", "name": "Campus Hostel Kitchen", "crop": "Tomato", "qty": 150, "price": 33, "lat": 17.558, "lng": 78.451},
    {"id": "B4", "name": "City Veg Retailer", "crop": "Onion", "qty": 250, "price": 29, "lat": 17.520, "lng": 78.510},
]


async def seed_buyers_if_empty():
    """Populate the buyers collection with demo data on first run."""
    count = await buyers_col.count_documents({})
    if count == 0:
        await buyers_col.insert_many(DEMO_BUYERS)


async def get_buyers_for_crop(crop: str):
    cursor = buyers_col.find({"crop": {"$regex": f"^{crop}$", "$options": "i"}})
    return [doc async for doc in cursor]
