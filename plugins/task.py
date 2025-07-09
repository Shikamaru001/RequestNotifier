from pyrogram import Client, filters
from db import config_dict, sync
from config import OWNER , LOGGER
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
import time , asyncio
from pyrogram.helpers import ikb , bki

async def delete_task(messages , time):
    
    await asyncio.sleep(time)

    for message in messages:
        try:
            await message.delete()
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            await message.delete()
        except Exception as e:
            pass

async def send_msg(client , chat_id):

    msg_ =  [config_dict[str(client.me.id)].get(f"MSG{i}", None) for i in range(1, 6)]
    photo_ =  [config_dict[str(client.me.id)].get(f"PHOTO{i}", None) for i in range(1, 6)]
    button_ =  [config_dict[str(client.me.id)].get(f"BUTTON{i}", None) for i in range(1, 6)]
    auto_delete = config_dict[str(client.me.id)]['AUTO_DELETE']
    protect = config_dict[str(client.me.id)]['PROTECT_CONTENT']

    for msg , photo , button in zip(msg_ , photo_ , button_):

        if not msg: continue

        reply_markup = None if not button else ikb(button)

        try:
            if not photo:
                done = await client.send_message(chat_id , msg , reply_markup=reply_markup , protect_content = protect)
            else:
                done = await client.send_photo(chat_id , photo , caption=msg , reply_markup=reply_markup , protect_content = protect)
            if auto_delete:
                asyncio.create_task(delete_task([done] , auto_delete))
        except FloodWait as e:
            if not photo:
                done = await client.send_message(chat_id , msg , reply_markup=reply_markup , protect_content = protect)
            else:
                done = await client.send_photo(chat_id , photo , caption=msg , reply_markup=reply_markup , protect_content = protect)
            if auto_delete:
                asyncio.create_task(delete_task([done] , auto_delete))

@Client.on_chat_join_request()
async def on_chat_join(client , message):

    my_id = str(client.me.id)
    
    from_user = message.from_user

    link = config_dict[my_id]['REQUEST_LINK'].get(str(message.chat.id))

    if not link:
        return
    
    if link != message.invite_link.invite_link: return
    
    if str(message.chat.id) not in config_dict[my_id]['REQUEST_COUNT']:
        config_dict[my_id]['REQUEST_COUNT'][str(message.chat.id)] = []

    if not from_user: return

    if from_user.id not in config_dict[my_id]['USERS']:
        config_dict[my_id]['USERS'].append(from_user.id)
        await sync()
    
    if from_user.id not in config_dict[my_id]['REQUEST_COUNT'][str(message.chat.id)]:
        config_dict[my_id]['REQUEST_COUNT'][str(message.chat.id)].append(from_user.id)
        await sync()

    await send_msg(client , from_user.id)

@Client.on_message(filters.create(lambda _,__,msg: msg.text and msg.text.startswith('/set_msg')))
async def set_msg(client , message):

    my_id = str(client.me.id)

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    reply = message.reply_to_message

    if not (reply and (reply.text or reply.photo) ) and ('delete' not in message.text or ''):
        try:
            return await message.reply_text("<b>Reply To Any Text Or Photo Message To Set As Join Message !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>Reply To Any Text Or Photo Message To Set As Join Message !</b>")

    splitted = message.text.split(maxsplit=1)

    index = splitted[0]

    if index == "/set_msg":
        index = "1"
    elif index == "/set_msg1":
        index = "1"
    else:
        try:
            index = int(index[-1])
            if index > 5:
                raise Exception()
            index = str(index)
        except:
            try:
                return await message.reply_text("<b>Use proper syntax like , /set_msg , /set_msg2 and upto /set_msg5 !</b>")
            except FloodWait as e:
                await asyncio.sleep(e.value * 1.2)
                return await message.reply_text("<b>Use proper syntax like , /set_msg , /set_msg2 and upto /set_msg5 !</b>")
    
    if len(splitted) > 1 and splitted[1].strip() == 'delete':
        try:
            del config_dict[my_id][f'MSG{index}']
            del config_dict[my_id][f'PHOTO{index}']
            del config_dict[my_id][f'BUTTON{index}']
        except:
            pass
        try:
            return await message.reply_text(f"<b>Message {index} Cleared !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text(f"<b>Message {index} Cleared !</b>")

    html_msg = (reply.text or reply.caption).html

    config_dict[my_id][f'MSG{index}'] = html_msg

    if reply.photo:
        config_dict[my_id][f'PHOTO{index}'] = reply.photo.file_id
    else:
        config_dict[my_id][f'PHOTO{index}'] = None
    
    if reply.reply_markup:
        config_dict[my_id][f'BUTTON{index}'] = bki(reply.reply_markup)
    else:
        config_dict[my_id][f'BUTTON{index}'] = None

    try:
        await message.reply_text(f'''<b>Join Message {index} Set Successfully !</b>''')
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(f'''<b>Join Message {index} Set Successfully !</b>''')

    await sync()

@Client.on_message(filters.command('get_link'))
async def get_link(client , message):

    my_id = str(client.me.id)

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()
    
    try:
        text = int(message.text.split(maxsplit = 1)[1])
    except IndexError:
        try:
            return await message.reply_text("<b>Provide Channel ID With Command To Get Request Link !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>Provide Channel ID With Command To Get Request Link !</b>")
    
    try:
        link = await client.create_chat_invite_link(
            chat_id = text,
            creates_join_request = True
        )
    except:
        try:
            return await message.reply_text("<b>Unable To Create Join Request Link , Make Sure I Have Rights!</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>Unable To Create Join Request Link , Make Sure I Have Rights !</b>")
    
    link = link.invite_link

    config_dict[my_id]['REQUEST_LINK'][str(text)] = link

    await sync()

    try:
        await message.reply_text(f"<b>Join Request Link Created Successfully !\n\nLink : {link}</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(f"<b>Join Request Link Created Successfully !\n\nLink : {link}</b>")

@Client.on_message(filters.command('get_msg'))
async def get_msg(client , message):

    my_id = str(client.me.id)

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    msg_ =  [config_dict[str(client.me.id)].get(f"MSG{i}", None) for i in range(1, 6)]

    if not any(msg_):
        try:
            return await message.reply_text("<b>No Join Message Set !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>No Join Message Set !</b>")
    
    try:
        await message.reply_text(f"<b>Below Is The Current Message -</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(f"<b>Below Is The Current Message -</b>")
    await send_msg(client , message.from_user.id)

@Client.on_message(filters.command('total_users'))
async def total_users(client , message):

    my_id = str(client.me.id)

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    total = config_dict[my_id]['USERS']

    if not total:
        try:
            return await message.reply_text("<b>No Users Found !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>No Users Found !</b>")
    
    try:
        await message.reply_text(f"<b>Total Users - {len(total)}</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(f"<b>Total Users - {len(total)}</b>")

@Client.on_message(filters.command('addadmin') & filters.private & filters.user(OWNER))
async def add_admin(client , message):

    my_id = str(client.me.id)

    try:
        user_id = int(message.text.split()[1])
    except IndexError:
        try:
            return await message.reply_text("<b>Provide User ID To Add As Admin With Command !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>Provide User ID To Add As Admin With Command !</b>")
    
    if user_id in config_dict[my_id]['ADMINS']:
        try:
            return await message.reply_text("<b>This User Is Already An Admin !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>This User Is Already An Admin !</b>")
    
    config_dict[my_id]['ADMINS'].append(user_id)

    await sync()

    try:
        await message.reply_text(f"<b>User ID {user_id} Added As Admin !</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(f"<b>User ID {user_id} Added As Admin !</b>")

@Client.on_message(filters.command('removeadmin') & filters.private & filters.user(OWNER))
async def remove_admin(client , message):

    my_id = str(client.me.id)

    try:
        user_id = int(message.text.split()[1])
    except IndexError:
        try:
            return await message.reply_text("<b>Provide User ID To Remove From Admins With Command !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>Provide User ID To Remove From Admins With Command !</b>")
    
    if user_id not in config_dict[my_id]['ADMINS']:
        try:
            return await message.reply_text("<b>This User Is Not An Admin !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>This User Is Not An Admin !</b>")
    
    config_dict[my_id]['ADMINS'].remove(user_id)

    await sync()

    try:
        await message.reply_text(f"<b>User ID {user_id} Removed From Admins !</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(f"<b>User ID {user_id} Removed From Admins !</b>")

@Client.on_message(filters.command('listadmins') & filters.private & filters.user(OWNER))
async def list_admins(client , message):
    my_id = str(client.me.id)

    admins = config_dict[my_id]['ADMINS']

    if not admins:
        try:
            return await message.reply_text("<b>No Admins Found !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>No Admins Found !</b>")
    
    admin_list = "\n".join([f"<code>{admin}</code>" for admin in admins])

    try:
        await message.reply_text(f"<b>Admins -\n{admin_list}</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(f"<b>Admins -\n{admin_list}</b>")

@Client.on_message(filters.command('auto_delete') & filters.private)
async def auto_delete(client , message):

    my_id = str(client.me.id)

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    try:
        time = int(message.text.split()[1])
    except IndexError:
        current_auto_delete = config_dict[my_id]['AUTO_DELETE']
        if not current_auto_delete:
            text = "<b>Provide Time In Seconds To Set Auto Delete With Command !</b>"
        else:
            text = f"<b>Auto Delete Time Is Currently Set To {current_auto_delete} Seconds !</b>"
        try:
            return await message.reply_text(text)
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text(text)
    
    config_dict[my_id]['AUTO_DELETE'] = time

    await sync()

    try:
        await message.reply_text(f"<b>Auto Delete Time Set To {time} Seconds !</b>")
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(f"<b>Auto Delete Time Set To {time} Seconds !</b>")

@Client.on_message(filters.command('protect') & filters.private)
async def protect(client , message):
    my_id = str(client.me.id)

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    if config_dict[my_id]['PROTECT_CONTENT']:
        config_dict[my_id]['PROTECT_CONTENT'] = False
        text = "<b>Protect Content Disabled !</b>"
    else:
        config_dict[my_id]['PROTECT_CONTENT'] = True
        text = "<b>Protect Content Enabled !</b>"
    
    await sync()

    try:
        await message.reply_text(text)
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(text)

@Client.on_message(filters.command('request_count') & filters.private)
async def request_count(client , message):

    my_id = str(client.me.id)

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()
    
    request_count = config_dict[my_id]['REQUEST_COUNT']

    if not request_count:
        try:
            return await message.reply_text("<b>No Request Count Found !</b>")
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>No Request Count Found !</b>")
    
    string = "<b>Request Counts -</b>\n\n"

    for chat_id , user_ids in request_count.items():
        string += f"<b>• {chat_id} - {len(user_ids)}</b>\n"
    
    try:
        await message.reply_text(string)
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text(string)

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

    my_id = str(client.me.id)

    if message.from_user.id not in config_dict[my_id]['ADMINS'] + OWNER:
        message.continue_propagation()

    reply = message.reply_to_message

    if not reply:
        try:
            return await message.reply_text("<b>Reply To Any Message To Broadcast !</b>" , quote=True)
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.2)
            return await message.reply_text("<b>Reply To Any Message To Broadcast !</b>" , quote=True)

    query = config_dict[my_id]['USERS']

    broadcast_msg = reply

    total , successful , blocked , deleted , unsuccessful = 0 , 0 , 0 , 0 , 0

    start_time = int(time.time())

    try:
        prog = await message.reply_text("<b>Broadcasting Message, Please Wait...</b>" , quote=True)
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        return await message.reply_text("<b>Broadcasting Message, Please Wait...</b>" , quote=True)

    status_msg = """<b><u>Broadcast {status}</u>

- Time Elapsed: <code>{elapsed}</code>

- Total Users: <code>{total}</code>
- Successful: <code>{successful}</code>
- Blocked Users: <code>{blocked}</code>
- Deleted Accounts: <code>{deleted}</code>
- Unsuccessful: <code>{unsuccessful}</code></b>"""

    for user_id in query:

        try:
            await broadcast_msg.copy(chat_id=user_id)
            successful += 1
        
        except FloodWait as e:
            await asyncio.sleep(e.value * 1.5)
            await broadcast_msg.copy(chat_id=user_id)
            successful += 1
        
        except UserIsBlocked:
            blocked += 1
        
        except InputUserDeactivated:
            deleted += 1
        
        except Exception as e:
            unsuccessful += 1
            LOGGER(__name__).info(f"ERROR Sending To User - {user_id} - {str(e)}")
        
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

            try:
                await prog.edit(status)
            except FloodWait as e:
                await asyncio.sleep(e.value * 1.2)
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
    try:
        await prog.edit(status)
    except FloodWait as e:
        await asyncio.sleep(e.value * 1.2)
        await prog.edit(status)

@Client.on_message(filters.private)
async def on_other_messages(client , message):

    my_id = str(client.me.id)

    if not message.from_user: return

    if message.from_user.id not in config_dict[my_id]['USERS']:
        config_dict[my_id]['USERS'].append(message.from_user.id)
        await sync()
    
    await send_msg(client , message.from_user.id)