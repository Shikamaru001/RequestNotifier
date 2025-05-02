from pyrogram import Client, filters , idle
from config import API_ID, API_HASH, BOT_TOKEN , LOGGER, OWNER
from db import config_dict, sync
import os , sys , asyncio

master = Client('master' , api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN , workers = 4)

master.start()

loop = master.loop

for bot_id in config_dict:
    if bot_id == "_id":
        continue
    
    bot_token = config_dict[bot_id]['BOT_TOKEN']
    
    try:
        temp = Client(
            str(bot_id) ,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token ,
            workers = 4 ,
            plugins= dict(root="plugins") ,
        )

        temp.start()

        me = temp.get_me()

        LOGGER(__name__).info(f"{me.first_name} ({me.id}) Started Successfully !")
    except:
        LOGGER(__name__).error(f"Failed To Start Bot - {bot_token}")

async def restart(done):
    with open(".restartmsg", "w") as f:
        f.write(f"{msg.chat.id}\n{msg.id}\n")
    os.execl(sys.executable, sys.executable, '-B' , "bot.py")

@master.on_message(filters.command('start') & filters.private & filters.user(OWNER))
async def start(client, message):
    await message.reply_text("<b>Hello! I am a master bot that manages other bots.</b>")

@master.on_message(filters.command('addbot') & filters.private & filters.user(OWNER))
async def add_bot(client, message):
    try:
        bot_token = message.text.split()[1]
    except IndexError:
        return await message.reply_text("<b>Please provide a bot token.</b>")
    
    bot_id = bot_token.split(":")[0]
    
    config_dict[bot_id] = {
        'BOT_TOKEN': bot_token,
        'MSG': None,
        'ADMINS': [],
        'USERS': []
    }

    await sync()

    done = await message.reply_text(f"<b>Bot with ID {bot_id} added successfully!\n\nNow Restarting All Bots!</b>")

    await restart(done)

async def restart_edit():
    if not os.path.exists(".restartmsg"):
        return
    with open(".restartmsg", "r") as f:
        data = f.read().splitlines()
    
    chat_id = int(data[0])
    msg_id = int(data[1])

    try:
        msg = await master.get_messages(chat_id , msg_id)

        await msg.edit(msg.text.html.replace('Now Restarting All Bots!' , 'All Bots Restarted Successfully !'))
    
    except:
        pass

loop.run_until_complete(restart_edit())

idle()