from config import MONGODB_URI, MONGODB_DB, LOGGER
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
    log = LOGGER(__name__)
    ids = []
    async for d in _bots_meta().find({}, {"_id": 1}):
        ids.append(str(d["_id"]))
    if ids:
        log.info(f"Found {len(ids)} bot ids in bots meta")
        return ids
    log.info("No entries in bots meta, falling back to scanning collections for settings documents")
    names = await database.list_collection_names()
    for name in names:
        if name.endswith("_USERS") or name == "bots":
            continue
        try:
            doc = await database[name].find_one({"_id": "settings"}, {"_id": 1})
        except Exception:
            doc = None
        if doc:
            ids.append(str(name))
    log.info(f"Found {len(ids)} bot ids by scanning collections")
    return ids

async def load_all_settings():
    global config_dict
    # do not rebind config_dict; clear and repopulate so importers keep reference
    config_dict.clear()
    log = LOGGER(__name__)
    names = await list_bot_ids()
    log.info(f"Loading settings for bot ids: {names}")
    for name in names:
        try:
            doc = await _settings_col(name).find_one({"_id": "settings"})
        except Exception as e:
            log.exception(f"Error reading settings for {name}: {e}")
            doc = None
        if not doc:
            log.warning(f"No settings document for bot {name}, skipping")
            continue
        data = dict(doc)
        data.pop("_id", None)
        # ensure required keys exist with sensible defaults
        defaults = {
            'BOT_TOKEN': data.get('BOT_TOKEN'),
            'BOT_USERNAME': data.get('BOT_USERNAME', None),
            'NAME': data.get('NAME', None),
            'REQUEST_LINK': data.get('REQUEST_LINK', {}) or {},
            'REQUEST_COUNT': data.get('REQUEST_COUNT', {}) or {},
            'PROTECT_CONTENT': data.get('PROTECT_CONTENT', False),
            'AUTO_DELETE': data.get('AUTO_DELETE', 0),
            'ADMINS': data.get('ADMINS', []) or [],
        }
        # merge defaults with stored data (stored values take precedence)
        merged = {**defaults, **data}
        # if token missing in settings, try to read it from bots meta
        if not merged.get('BOT_TOKEN'):
            try:
                meta = await _bots_meta().find_one({"_id": name})
            except Exception:
                meta = None
            if meta and meta.get('token'):
                merged['BOT_TOKEN'] = meta.get('token')
        config_dict[str(name)] = merged
    log.info(f"Loaded settings for {len(config_dict)} bots: {list(config_dict.keys())}")

async def get_bots_meta():
    """Return list of bot ids from meta collection (for debug)."""
    out = []
    async for d in _bots_meta().find({}, {"_id": 1, "token": 1}):
        out.append({"id": str(d.get("_id")), "token": d.get("token")})
    return out

async def save_settings(bot_id: str):
    data = dict(config_dict[str(bot_id)])
    await _settings_col(bot_id).update_one({"_id": "settings"}, {"$set": data}, upsert=True)
    LOGGER(__name__).info(f"Saved settings for bot {bot_id}")

async def create_bot(bot_id: str, settings: dict):
    await _settings_col(bot_id).update_one({"_id": "settings"}, {"$set": settings}, upsert=True)
    await _bots_meta().update_one({"_id": str(bot_id)}, {"$set": {"token": settings.get("BOT_TOKEN")}}, upsert=True)
    config_dict[str(bot_id)] = settings
    LOGGER(__name__).info(f"Created bot {bot_id} in DB and updated meta collection")

async def delete_bot(bot_id: str):
    await database.drop_collection(str(bot_id))
    await database.drop_collection(f"{bot_id}_USERS")
    await _bots_meta().delete_one({"_id": str(bot_id)})
    config_dict.pop(str(bot_id), None)
    LOGGER(__name__).info(f"Deleted bot {bot_id} and its collections from DB")

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

async def ping_db():
    await client.admin.command("ping")