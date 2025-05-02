from pyrogram import Client, filters
from db import config_dict, sync
from config import OWNER
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
import time , asyncio
from pyrogram.helpers import ikb , bki

async def send_msg(client , chat_id):

    msg = config_dict[client.me.id]['MSG']
    photo = config_dict[client.me.id]['PHOTO']
    button = config_dict[client.me.id]['BUTTON']

    if not msg: return False

    reply_markup = None if not button else ikb(button)

    if not PHOTO:
        await client.send_message(chat_id , msg , reply_markup=reply_markup)
    else:
        await client.send_photo(chat_id , photo , caption=msg , reply_markup=reply_markup)
    return True

@Client.on_chat_join_request()
async def on_chat_join(client , message):
    
    from_user = message.from_user

    if not from_user: return

    if from_user.id not in config_dict[my_id]['USERS']:
        config_dict[my_id]['USERS'].append(from_user.id)
        await sync()

    await send_msg(client , from_user.id)

@Client.on_message(filters.command('set_msg'))
async def set_msg(client , message):

    my_id = client.me.id

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    reply = message.reply_to_message

    if not (reply and (reply.text or reply.photo)):
        return await message.reply_text("<b>Reply To Any Text Or Photo Message To Set As Join Message !</b>")
    
    html_msg = (reply.text or reply.caption).html

    config_dict[my_id]['MSG'] = html_msg

    if reply.photo:
        config_dict[my_id]['PHOTO'] = reply.photo.file_id
    
    if reply.reply_markup:
        config_dict[my_id]['BUTTON'] = bki(reply.reply_markup)

    await message.reply_text(f'''<b>Join Message Set Successfully !</b>''')

    await sync()

@Client.on_message(filters.command('get_msg'))
async def get_msg(client , message):

    my_id = client.me.id

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    msg = config_dict[my_id]['MSG']

    if not msg:
        return await message.reply_text("<b>No Join Message Set !</b>")
    
    await message.reply_text(f"<b>Below Is The Current Message -</b>")
    await send_msg(client , message.from_user.id)

@Client.on_message(filters.command('total_users'))
async def total_users(client , message):

    my_id = client.me.id

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    total = config_dict[my_id]['USERS']

    if not total:
        return await message.reply_text("<b>No Users Found !</b>")
    
    await message.reply_text(f"<b>Total Users - {len(total)}</b>")

@Client.on_message(filters.command('addadmin') & filters.private & filters.user(OWNER))
async def add_admin(client , message):

    my_id = client.me.id

    try:
        user_id = int(message.text.split()[1])
    except IndexError:
        return await message.reply_text("<b>Provide User ID To Add As Admin !</b>")
    
    if user_id in config_dict[my_id]['ADMINS']:
        return await message.reply_text("<b>This User Is Already An Admin !</b>")
    
    config_dict[my_id]['ADMINS'].append(user_id)

    await sync()

    await message.reply_text(f"<b>User ID {user_id} Added As Admin !</b>")

@Client.on_message(filters.command('removeadmin') & filters.private & filters.user(OWNER))
async def remove_admin(client , message):

    my_id = client.me.id

    try:
        user_id = int(message.text.split()[1])
    except IndexError:
        return await message.reply_text("<b>Provide User ID To Remove From Admins !</b>")
    
    if user_id not in config_dict[my_id]['ADMINS']:
        return await message.reply_text("<b>This User Is Not An Admin !</b>")
    
    config_dict[my_id]['ADMINS'].remove(user_id)

    await sync()

    await message.reply_text(f"<b>User ID {user_id} Removed From Admins !</b>")

@Client.on_message(filters.command('listadmins') & filters.private & filters.user(OWNER))
async def list_admins(client , message):
    my_id = client.me.id

    admins = config_dict[my_id]['ADMINS']

    if not admins:
        return await message.reply_text("<b>No Admins Found !</b>")
    
    admin_list = "\n".join([f"<code>{admin}</code>" for admin in admins])

    await message.reply_text(f"<b>Admins -\n{admin_list}</b>")

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

@Client.on_message(filters.private & filters.command('broadcast'))
async def on_broadcast(client , message):

    my_id = client.me.id

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    reply = message.reply_to_message

    if not reply:
         return await message.reply_text("<b>Reply To Any Message To Broadcast !</b>" , quote=True)

    query = config_dict[my_id]['USERS']

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
            if user_id in config_dict[my_id]['USERS']:
                config_dict[my_id]['USERS'].remove(user_id)
                await sync()
            blocked += 1
        
        except InputUserDeactivated:
            if user_id in config_dict[my_id]['USERS']:
                config_dict[my_id]['USERS'].remove(user_id)
                await sync()
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

@Client.on_message(filters.private)
async def on_other_messages(client , message):

    if not message.from_user: return

    if message.from_user.id not in config_dict[my_id]['USERS']:
        config_dict[my_id]['USERS'].append(message.from_user.id)
        await sync()
    
    await send_msg(client , message.from_user.id)