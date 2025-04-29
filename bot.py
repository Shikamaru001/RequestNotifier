from pyrogram import Client, filters , idle
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from config import API_ID, API_HASH, BOT_TOKEN , ADMINS , LOGGER
from db import config_dict, sync , add_user , delete_user
import time , asyncio
from pyrogram.types import BotCommand

app = Client('bot' , api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN , workers = 10)

app.start()

loop = app.loop

bot_cmds = [
    BotCommand("set_msg", "Set Message To Send On Join (Admins)"),
    BotCommand("get_msg", "Get Current Join Message (Admins)"),
    BotCommand("total_users", "Get Total Users (Admins)"),
    BotCommand("broadcast", "Broadcast To All Users (Owner Only)"),
]

@app.on_chat_join_request()
async def on_chat_join(client , message):

    msg = config_dict['MSG']

    if not msg:
        return
    
    from_user = message.from_user

    if not from_user: return

    await add_user(from_user.id)

    await client.send_message(from_user.id , msg)

@app.on_message(filters.command('set_msg') & filters.user(ADMINS))
async def set_msg(client , message):

    reply = message.reply_to_message

    if not (reply and reply.text):
        return await message.reply_text("<b>Reply To Any Text Message To Set As Join Message !</b>")
    
    html_msg = reply.text.html

    config_dict['MSG'] = html_msg

    await message.reply_text(f'''<b>Join Message Set Successfully -
    
<code>{html_msg}</code></b>''')

    await sync()

@app.on_message(filters.command('get_msg') & filters.user(ADMINS))
async def get_msg(client , message):

    msg = config_dict['MSG']

    if not msg:
        return await message.reply_text("<b>No Join Message Set !</b>")
    
    await message.reply_text(f'''<b>Current Join Message -

<code>{msg}</code></b>''')

@app.on_message(filters.command('total_users') & filters.user(ADMINS))
async def total_users(client , message):

    total = config_dict['USERS']

    if not total:
        return await message.reply_text("<b>No Users Found !</b>")
    
    await message.reply_text(f"<b>Total Users - {len(total)}</b>")

async def convertTime(s: int) -> str:
    m, s = divmod(int(s), 60)
    hr, m = divmod(m, 60)
    days, hr = divmod(hr, 24)
    convertedTime = (
        (f"{int(days)} days, " if days else "")
        + (f"{int(hr)} hours, " if hr else "")
        + (f"{int(m)} minutes, " if m else "")
        + (f"{int(s)} seconds, " if s else "")
    )
    return convertedTime[:-2]

@app.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def on_broadcast(client , message):

    reply = message.reply_to_message

    if not reply:
         return await message.reply_text("<b>Reply To Any Message To Broadcast !</b>" , quote=True)

    query = config_dict['USERS']

    broadcast_msg = reply

    broadcast_reply_markup = reply.reply_markup

    total , successful , blocked , deleted , unsuccessful = 0 , 0 , 0 , 0 , 0

    start_time = int(time.time())

    prog = await message.reply_text("<b>Broadcasting Message, Please Wait...</b>" , quote=True)

    status_msg = """<b><u>Broadcast {status}</u>

- Time Elapsed: <code>{elapsed}</code>

- Total Users: <code>{total}</code>
- Successful: <code>{successful}</code>
- Blocked Users: <code>{blocked}</code>
- Deleted Accounts: <code>{deleted}</code>
- Unsuccessful: <code>{unsuccessful}</code></b>"""

    for user_id in query:

        try:
            await broadcast_msg.copy(chat_id=user_id , reply_markup=broadcast_reply_markup)
            successful += 1
        
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.5)
            await broadcast_msg.copy(chat_id=user_id , reply_markup=broadcast_reply_markup)
            successful += 1
        
        except UserIsBlocked:
            await delete_user(user_id)
            blocked += 1
        
        except InputUserDeactivated:
            await delete_user(user_id)
            deleted += 1
        
        except Exception as e:
            unsuccessful += 1
        
        total += 1

        if total % 20 == 0:

            elapsed_time = await convertTime(int(time.time() - start_time))

            status = status_msg.format(
                status = "In Progress",
                elapsed = elapsed_time,
                total = total,
                successful = successful,
                blocked = blocked,
                deleted = deleted,
                unsuccessful = unsuccessful
            )

            await prog.edit(status)

            await asyncio.sleep(1)
    
    elapsed_time = await convertTime(int(time.time() - start_time))
    status = status_msg.format(
        status = "Completed",
        elapsed = elapsed_time,
        total = total,
        successful = successful,
        blocked = blocked,
        deleted = deleted,
        unsuccessful = unsuccessful
    )
    await prog.edit(status)

@app.on_message(filters.private)
async def on_other_messages(client , message):

    if not message.from_user: return

    await add_user(message.from_user.id)

    msg = config_dict['MSG']

    if not msg:
        return
    
    await message.reply_text(msg)

LOGGER(__name__).info("Bot Started Successfully !")
idle()