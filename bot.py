from pyrogram import Client, filters, idle
from config import API_ID, API_HASH, BOT_TOKEN, LOGGER, OWNER
from db import config_dict, load_all_settings, save_settings, create_bot, delete_bot, add_user, user_exists, count_users, ping_db
import os, sys, asyncio
from pyrogram.types import BotCommand
from pyrogram.errors import FloodWait

master = Client('master', api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=4)
workers = {}

loop = asyncio.get_event_loop()

async def start_worker_bots():
    LOGGER(__name__).info("start_worker_bots: loading settings from DB")
    await load_all_settings()
    print(config_dict.keys())
    LOGGER(__name__).info(f"config_dict after load: keys={list(config_dict.keys())} len={len(config_dict)}")
    try:
        metas = await __import__('db').db.get_bots_meta()
    except Exception:
        try:
            from db import get_bots_meta
            metas = await get_bots_meta()
        except Exception:
            metas = None
    LOGGER(__name__).info(f"bots meta: {metas}")
    for bot_id in list(config_dict.keys()):
        bot_token = config_dict[bot_id].get('BOT_TOKEN')
        LOGGER(__name__).info(f"starting worker for bot_id={bot_id} bot_token_present={bool(bot_token)}")
        try:
            LOGGER(__name__).info(f"starting worker for bot_id={bot_id} token_mask={str(bot_token)[:10]}...")
            temp = Client(
                str(bot_id),
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot_token,
                workers=4,
                plugins=dict(root="plugins"),
            )
            await temp.start()
            workers[str(bot_id)] = temp
            bot_cmds = [
                BotCommand("set_msg", "Set Message To Send On Join (Admins Only)"),
                BotCommand("get_msg", "Get Current Join Message (Admins Only)"),
                BotCommand("total_users", "Get Total Users (Admins Only)"),
                BotCommand("get_link", "Get Request Link (Admins Only)"),
                BotCommand("request_count", "Get Request Count For All Channels (Admins Only)"),
                BotCommand("auto_delete", "Set Auto Delete Time (Admins Only)"),
                BotCommand("protect", "Protect Content (Admins Only)"),
                BotCommand("broadcast", "Broadcast To All Users (Admins Only)"),
                BotCommand("addadmin", "Add Admin (Owner Only)"),
                BotCommand("removeadmin", "Remove Admin (Owner Only)"),
                BotCommand("listadmins", "List All Admins (Owner Only)"),
            ]
            try:
                await temp.set_bot_commands(bot_cmds)
            except FloodWait as e:
                await asyncio.sleep(e.value * 1.2)
                await temp.set_bot_commands(bot_cmds)
            me = await temp.get_me()
            temp.me = me
            if not config_dict[bot_id].get('NAME'):
                config_dict[bot_id]['NAME'] = me.first_name
            if not config_dict[bot_id].get('BOT_USERNAME'):
                config_dict[bot_id]['BOT_USERNAME'] = me.username
            await save_settings(bot_id)
            LOGGER(__name__).info(f"{me.first_name} ({me.id}) Started Successfully !")
        except Exception as e:
            LOGGER(__name__).exception(f"Failed To Start Bot - bot_id={bot_id} token_mask={str(bot_token)[:10]}: {e}")

async def restart(done):
    with open(".restartmsg", "w") as f:
        f.write(f"{done.chat.id}\n{done.id}\n")
    os.execl(sys.executable, sys.executable, '-B' , "bot.py")

@master.on_message(filters.command('start') & filters.private)
async def start(client, message):
    await message.reply_text("<b>Hello! I Am Master Bot That Manages Other Bots !</b>")

@master.on_message(filters.command('addbot') & filters.private & filters.user(OWNER))
async def add_bot(client, message):
    try:
        bot_token = message.text.split()[1]
    except IndexError:
        return await message.reply_text("<b>Please Provide Bot Token With Command .\n\nSyntax : <code>/addbot bot_token</code></b>")
    
    bot_id = bot_token.split(":")[0]
    settings = {
        'BOT_TOKEN': bot_token,
        'BOT_USERNAME': None,
        'NAME': None,
        'REQUEST_LINK': {},
        'REQUEST_COUNT': {},
        'PROTECT_CONTENT': False,
        'AUTO_DELETE': 0,
        'ADMINS': []
    }
    await create_bot(bot_id, settings)
    config_dict[bot_id] = settings
    LOGGER(__name__).info(f"add_bot: created bot {bot_id} in DB")

    try:
        done = await message.reply_text(f"<b>Bot with ID {bot_id} added successfully! Starting now...</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        done = await message.reply_text(f"<b>Bot with ID {bot_id} added successfully! Starting now...</b>")
    try:
        temp = Client(
            str(bot_id),
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=bot_token,
            workers=4,
            plugins=dict(root="plugins"),
        )
        await temp.start()
        workers[str(bot_id)] = temp
        bot_cmds = [
            BotCommand("set_msg", "Set Message To Send On Join (Admins Only)"),
            BotCommand("get_msg", "Get Current Join Message (Admins Only)"),
            BotCommand("total_users", "Get Total Users (Admins Only)"),
            BotCommand("get_link", "Get Request Link (Admins Only)"),
            BotCommand("request_count", "Get Request Count For All Channels (Admins Only)"),
            BotCommand("auto_delete", "Set Auto Delete Time (Admins Only)"),
            BotCommand("protect", "Protect Content (Admins Only)"),
            BotCommand("broadcast", "Broadcast To All Users (Admins Only)"),
            BotCommand("addadmin", "Add Admin (Owner Only)"),
            BotCommand("removeadmin", "Remove Admin (Owner Only)"),
            BotCommand("listadmins", "List All Admins (Owner Only)"),
        ]
        try:
            await temp.set_bot_commands(bot_cmds)
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            await temp.set_bot_commands(bot_cmds)
        me = await temp.get_me()
        temp.me = me
        if not config_dict[bot_id].get('NAME'):
            config_dict[bot_id]['NAME'] = me.first_name
        if not config_dict[bot_id].get('BOT_USERNAME'):
            config_dict[bot_id]['BOT_USERNAME'] = me.username
        await save_settings(bot_id)
        try:
            await done.edit(f"<b>Bot {me.first_name} ({me.id}) started successfully.</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            await done.edit(f"<b>Bot {me.first_name} ({me.id}) started successfully.</b>")
    except Exception as e:
        LOGGER(__name__).exception(f"add_bot: failed to start worker for bot_id={bot_id}: {e}")
        try:
            await done.edit("<b>Failed to start the bot, check token and logs.</b>")
        except Exception:
            pass

@master.on_message(filters.command('removebot') & filters.private & filters.user(OWNER))
async def remove_bot(client, message):
    try:
        bot_id = message.text.split()[1]
    except IndexError:
        return await message.reply_text("<b>Please Provide Bot ID With Command.\n\nSyntax : <code>/removebot bot_id</code></b>")
    
    if bot_id not in config_dict:
        return await message.reply_text("<b>Bot Not Added.</b>")
    await delete_bot(bot_id)
    LOGGER(__name__).info(f"remove_bot: deleted bot {bot_id} from DB")

    done = await message.reply_text(f"<b>Bot with ID {bot_id} removed successfully!\n\nNow Restarting All Bots!</b>")

    await restart(done)

@master.on_message(filters.command('listbots') & filters.private & filters.user(OWNER))
async def list_bots(client, message):
    await load_all_settings()
    copy = config_dict.copy()
    if not copy:
        return await message.reply_text("<b>No bots found.</b>")
    
    string = "<b>List of Bots:</b>\n\n"

    for bot_id in copy:
        string += f"<b>Bot : [{copy[bot_id]['NAME']}](t.me/{copy[bot_id]['BOT_USERNAME']})\n"
        string += f"<b>Bot Token:</b> <code>{copy[bot_id]['BOT_TOKEN']}</code>\n\n"
    string += "<b>Use /removebot <bot_id> to remove a bot.</b>"

    await message.reply_text(string)

@master.on_message(filters.command('restart') & filters.private & filters.user(OWNER))
async def restart_(client, message):
    msg = await message.reply_text('<b><i>Now Restarting All Bots!</i></b>' , True)
    with open(".restartmsg", "w") as f:
        f.write(f"{msg.chat.id}\n{msg.id}\n")
    os.execl(sys.executable, sys.executable, '-B' , "bot.py")

@master.on_message(filters.command('log') & filters.private & filters.user(OWNER))
async def log(client, message):

    await message.reply_document('log.txt', caption='<b>LOG File</b>' , quote =True)

async def restart_edit():
    if not os.path.exists(".restartmsg"):
        return
    with open(".restartmsg", "r") as f:
        data = f.read().splitlines()
    
    chat_id = int(data[0])
    msg_id = int(data[1])

    try:
        msg = await master.get_messages(chat_id , msg_id)
        if msg and msg.text:
            await msg.edit(msg.text.replace('Now Restarting All Bots!' , 'All Bots Restarted Successfully !'))
        os.remove(".restartmsg")
    except:
        pass

async def set_commands():
    bot_cmds = [
        BotCommand("start", "Start the bot"),
        BotCommand("addbot", "Add a new bot (Owner only)"),
        BotCommand("removebot", "Remove an existing bot (Owner only)"),
        BotCommand("listbots", "List all bots (Owner only)"),
        BotCommand("restart", "Restart all bots (Owner only)"),
    ]
    try:
        await master.set_bot_commands(bot_cmds)
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        await master.set_bot_commands(bot_cmds)

async def main():
    await master.start()
    try:
        await ping_db()
    except Exception:
        await asyncio.sleep(1)
        await ping_db()
    await start_worker_bots()
    await restart_edit()
    await load_all_settings()
    await set_commands()
    LOGGER(__name__).info("Master Bot Started Successfully !")
    await idle()

loop.run_until_complete(main())