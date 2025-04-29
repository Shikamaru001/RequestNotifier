from config import MONGODB_URI , MONGODB_DB
from pymongo import MongoClient
import asyncio

client = MongoClient(MONGODB_URI)
database = client[MONGODB_DB]
col = database[MONGODB_DB]

config_dict = col.find_one({'_id': MONGODB_DB })

if not config_dict:
    config_dict = {'_id' : MONGODB_DB}
    col.insert_one(config_dict)

if 'USERS' not in config_dict: config_dict['USERS'] = []
if 'MSG' not in config_dict: config_dict['MSG'] = None

lock = asyncio.Lock()

async def sync():
    async with lock:
        col.replace_one({'_id': MONGODB_DB }, config_dict )

async def add_user(user_id):
    if user_id not in config_dict['USERS']:
        config_dict['USERS'].append(user_id)
        await sync()

async def delete_user(user_id):
    if user_id in config_dict['USERS']:
        config_dict['USERS'].remove(user_id)
        await sync()