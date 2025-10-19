from config import MONGODB_URI, MONGODB_DB
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(MONGODB_URI)
database = client[MONGODB_DB]

config_dict = {}

def _settings_col(bot_id: str):
    return database[str(bot_id)]

def _users_col(bot_id: str):
    return database[f"{bot_id}_USERS"]

def _bots_meta():
    return database["bots"]

async def list_bot_ids():
    ids = []
    async for d in _bots_meta().find({}, {"_id": 1}):
        ids.append(str(d["_id"]))
    if ids:
        return ids
    names = await database.list_collection_names()
    for name in names:
        if name.endswith("_USERS") or name == "bots":
            continue
        doc = await database[name].find_one({"_id": "settings"}, {"_id": 1})
        if doc:
            ids.append(str(name))
    return ids

async def load_all_settings():
    global config_dict
    config_dict = {}
    names = await list_bot_ids()
    for name in names:
        doc = await _settings_col(name).find_one({"_id": "settings"})
        if doc:
            data = dict(doc)
            data.pop("_id", None)
            config_dict[str(name)] = data

async def save_settings(bot_id: str):
    data = dict(config_dict[str(bot_id)])
    await _settings_col(bot_id).update_one({"_id": "settings"}, {"$set": data}, upsert=True)

async def create_bot(bot_id: str, settings: dict):
    await _settings_col(bot_id).update_one({"_id": "settings"}, {"$set": settings}, upsert=True)
    await _bots_meta().update_one({"_id": str(bot_id)}, {"$set": {"token": settings.get("BOT_TOKEN")}}, upsert=True)
    config_dict[str(bot_id)] = settings

async def delete_bot(bot_id: str):
    await database.drop_collection(str(bot_id))
    await database.drop_collection(f"{bot_id}_USERS")
    await _bots_meta().delete_one({"_id": str(bot_id)})
    config_dict.pop(str(bot_id), None)

async def add_user(bot_id: str, user_id: int):
    try:
        await _users_col(bot_id).insert_one({"_id": int(user_id)})
    except Exception:
        pass

async def user_exists(bot_id: str, user_id: int) -> bool:
    doc = await _users_col(bot_id).find_one({"_id": int(user_id)}, {"_id": 1})
    return doc is not None

async def count_users(bot_id: str) -> int:
    return await _users_col(bot_id).count_documents({})

async def iter_user_ids(bot_id: str):
    cursor = _users_col(bot_id).find({}, {"_id": 1})
    async for d in cursor:
        yield d["_id"]