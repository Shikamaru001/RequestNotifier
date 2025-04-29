import logging
from logging.handlers import RotatingFileHandler
from os import environ
from dotenv import load_dotenv

load_dotenv(".env")

# BOT SETTINGS
API_ID = environ.get("API_ID", "")
API_HASH = environ.get("API_HASH", "")
BOT_TOKEN = environ.get("BOT_TOKEN", "")

MONGODB_URI = environ.get("MONGODB_URI", "")
MONGODB_DB = environ.get("MONGODB_DB", "")

ADMINS = [ int(x) for x in (environ.get("ADMINS", "") or "").split() ]

#LOGGING
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            'log.txt',
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)