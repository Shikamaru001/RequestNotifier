from pyrogram import Client, filters , idle
from config import API_ID, API_HASH, BOT_TOKEN , LOGGER, OWNER
from db import config_dict, sync
import os , sys , asyncio
from pyrogram.types import BotCommand

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

        bot_cmds = [
            BotCommand("set_msg", "Set Message To Send On Join (Admins Only)"),
            BotCommand("get_msg", "Get Current Join Message (Admins Only)"),
            BotCommand("total_users", "Get Total Users (Admins Only)"),
            BotCommand("broadcast", "Broadcast To All Users (Admins Only)"),
            BotCommand("addadmin", "Add Admin (Owner Only)"),
            BotCommand("removeadmin", "Remove Admin (Owner Only)"),
            BotCommand("listadmins", "List All Admins (Owner Only)"),
        ]

        temp.set_bot_commands(bot_cmds)

        me = temp.get_me()

        temp.me = me

        if 'NAME' not in config_dict[bot_id]:
            config_dict[bot_id]['NAME'] = me.first_name

        LOGGER(__name__).info(f"{me.first_name} ({me.id}) Started Successfully !")
    except:
        LOGGER(__name__).error(f"Failed To Start Bot - {bot_token}")

async def restart(done):
    with open(".restartmsg", "w") as f:
        f.write(f"{done.chat.id}\n{done.id}\n")
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

@master.on_message(filters.command('removebot') & filters.private & filters.user(OWNER))
async def remove_bot(client, message):
    try:
        bot_id = message.text.split()[1]
    except IndexError:
        return await message.reply_text("<b>Please provide a bot ID.</b>")
    
    if bot_id not in config_dict:
        return await message.reply_text("<b>Bot ID not found.</b>")
    
    del config_dict[bot_id]

    await sync()

    done = await message.reply_text(f"<b>Bot with ID {bot_id} removed successfully!\n\nNow Restarting All Bots!</b>")

    await restart(done)

@master.on_message(filters.command('listbots') & filters.private & filters.user(OWNER))
async def list_bots(client, message):
    copy = config_dict.copy()
    del copy["_id"]
    if not copy:
        return await message.reply_text("<b>No bots found.</b>")
    
    string = "<b>List of Bots:</b>\n\n"

    for bot_id in copy:
        string += f"<b>Bot ID:</b> {bot_id}\n"
        string += f"<b>Bot Token:</b> {copy[bot_id]['BOT_TOKEN']}\n"
        string += f"<b>Bot Name:</b> {copy[bot_id].get('NAME', 'N/A')}\n\n"
    string += "<b>Use /removebot <bot_id> to remove a bot.</b>"

    await message.reply_text(string)

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
        os.remove(".restartmsg")
    except:
        pass

async def set_commands():
    bot_cmds = [
        BotCommand("addbot", "Add a new bot (Owner only)"),
        BotCommand("removebot", "Remove an existing bot (Owner only)"),
        BotCommand("listbots", "List all bots (Owner only)"),
    ]
    await master.set_bot_commands(bot_cmds)

loop.run_until_complete(restart_edit())
loop.run_until_complete(set_commands())
LOGGER(__name__).info("Master Bot Started Successfully !")
idle()