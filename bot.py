import os
import asyncio
from telethon import TelegramClient, events, functions, types

# ===== إعدادات البوت =====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@sutazz")

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# القوائم
pending_users = {}    # الأعضاء المعلقين على الانضمام للقناة
restricted_users = {} # الأعضاء المقيدين حاليًا

# ===== مراقبة الرسائل الجديدة في المجموعة =====
@client.on(events.NewMessage)
async def restrict_member(event):
    if event.is_private:
        return

    sender = await event.get_sender()
    user_id = sender.id
    chat_id = event.chat_id

    # لو العضو موجود مسبقًا في pending_users لا نعيد تقييده
    if user_id in pending_users:
        return

    # تقييد العضو فورًا
    await client.edit_permissions(chat_id, user_id, send_messages=False)
    restricted_users[user_id] = chat_id
    pending_users[user_id] = chat_id

    # إرسال رسالة التحذير
    await event.reply(
        f'عزيزي @{sender.username if sender.username else sender.first_name} '
        f'يجب عليك الانضمام في القناة طـز ثم تابع كلامك معنا نحن بانتظارك {CHANNEL_USERNAME}'
    )

# ===== فحص القناة كل 10 ثواني =====
async def check_channel():
    while True:
        to_remove = []
        for user_id, chat_id in pending_users.items():
            try:
                participant = await client(functions.channels.GetParticipantRequest(
                    channel=CHANNEL_USERNAME,
                    participant=user_id
                ))
                if isinstance(participant.participant, (types.ChannelParticipant, types.ChannelParticipantSelf)):
                    # فتح إرسال الرسائل
                    await client.edit_permissions(chat_id, user_id, send_messages=True)
                    # إزالة العضو من القوائم
                    to_remove.append(user_id)
                    if user_id in restricted_users:
                        restricted_users.pop(user_id)
            except:
                pass
        for user_id in to_remove:
            pending_users.pop(user_id)
        await asyncio.sleep(10)

# ===== أمر /start =====
@client.on(events.NewMessage(pattern="/start"))
async def start_command(event):
    await event.respond("✅ البوت يعمل بنجاح!")

# ===== أمر /pending =====
@client.on(events.NewMessage(pattern="/pending"))
async def show_pending(event):
    if not pending_users:
        await event.respond("لا يوجد أعضاء معلقين حاليًا ✅")
        return

    msg = "📋 قائمة الأعضاء المعلقين:\n"
    for user_id in pending_users:
        try:
            user = await client.get_entity(user_id)
            username = f"@{user.username}" if user.username else user.first_name
            msg += f"- {username} (ID: {user_id})\n"
        except:
            msg += f"- Unknown (ID: {user_id})\n"
    await event.respond(msg)

# ===== أمر /restricted =====
@client.on(events.NewMessage(pattern="/restricted"))
async def show_restricted(event):
    if not restricted_users:
        await event.respond("لا يوجد أعضاء مقيدين حاليًا ✅")
        return

    msg = "📋 قائمة الأعضاء المقيدين:\n"
    for user_id in restricted_users:
        try:
            user = await client.get_entity(user_id)
            username = f"@{user.username}" if user.username else user.first_name
            msg += f"- {username} (ID: {user_id})\n"
        except:
            msg += f"- Unknown (ID: {user_id})\n