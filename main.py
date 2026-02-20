from telethon import TelegramClient, events, Button
from telethon.tl.functions.messages import SendReactionRequest
from telethon.tl.types import ReactionEmoji
from telethon.sessions import StringSession, MemorySession
from telethon.errors import SessionPasswordNeededError
import asyncio
import logging
import re
import os

# === الإعدادات الأساسية ===
API_ID = 30421842
API_HASH = "bfed8c6f671c1cc4db37cc479bcac370"
OWNER_ID = 8258889952
BOT_TOKEN = "8346148314:AAFYJub4rcAWprFFewqJYTOhx1HSftCRWfU"

WORKER_TOKENS = [
    "8303573438:AAF2MRf3tQR23EhOp2JeZ53YJR6c6EMSVLM", "8536499718:AAH_2LKA_hbMj4ep57PCRX-dKwv8cuZbRSI",
    "8259037864:AAGu7hUmRFN2XP7TJIbJ2waKH75HIcXZMBY", "8438984859:AAEw624vfUVMe_y6n1alHzhYuZKAMktYMMU",
    "8588891233:AAHjofIVmMNJ06FOGCk_ejxb2lySK-6NSaU", "8204505036:AAFpCXPM8C_TwzKGpKnq4t8MOCpd70ry5Js",
    "8311486512:AAHAEAxOHdmanLzvj4zRso3RNtMOMVkARt8", "8359169296:AAFlvLsANXkLNPjfpPzjk0MA11HBkBVZzBc",
    "8288166544:AAGVshxBvERyPJZRckR010uE9baCHKRM_9E", "8577728976:AAFWRbiJdpdbl1WHIrAA86TCdPrws8XcYVk",
    "8358087517:AAHDBidKo4m4njVfkv6rOxbsw6vDqLaojhM", "8268512160:AAFG6oy8Fq4bDqFwTt_tHSsJDjxAqXpyUII"
]

BOT_EMOJIS = ["❤️","👏","❤️‍🔥","💯","🔥","🕊️","🍓","😭","💘","🗿","👌","🙏","💔","🤝"]
USER_EMOJIS = ["🕊️","😁","🤔","👍","🙏","💯","🗿","🫡","😐","👀","⚡","🤝","✍️","💘","❤️‍🔥","👏","🍓","🤝","👌"]

logging.basicConfig(level=logging.ERROR)

worker_clients = []
user_accounts = [] 
main_bot = TelegramClient(MemorySession(), API_ID, API_HASH)

user_state = {}
group_delays = {}  # تخزين الوقت بالثواني لكل مجموعة
SESSIONS_FILE = "sessions.txt"

def save_session(s):
    try:
        with open(SESSIONS_FILE, "a") as f: f.write(s + "\n")
    except: pass

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r") as f: return [l.strip() for l in f.readlines() if l.strip()]
    return []

async def init_accounts():
    sessions = load_sessions()
    for s in sessions:
        try:
            c = TelegramClient(StringSession(s), API_ID, API_HASH)
            await c.connect()
            if await c.is_user_authorized(): user_accounts.append(c)
        except: pass

async def send_react(client, chat, msg_id, emoji):
    try:
        await client(SendReactionRequest(peer=chat, msg_id=msg_id, reaction=[ReactionEmoji(emoticon=emoji)]))
        return True
    except: return False

def get_link(chat, mid):
    cid = str(chat).replace("-100", "") if isinstance(chat, int) else chat
    return f"https://t.me/c/{cid}/{mid}"

def parse_link(text):
    m = re.search(r"t\.me/(?:c/)?([^/]+)/(\d+)", text)
    if m:
        c, mid = m.group(1), int(m.group(2))
        if "/c/" in text: c = int("-100" + str(c))
        return c, mid
    return None, None

def get_group_buttons(chat=None, mid=None, mode="bot"):
    if mode == "bot":
        return [[Button.inline(f"🤖 مجموعة البوتات {i+1}", data=f"lst_b_{chat}_{mid}_{i}")] for i in range(3)]
    elif mode == "user":
        num_groups = (len(user_accounts) + 3) // 4
        return [[Button.inline(f"👤 مجموعة الحسابات {i+1}", data=f"lst_u_{chat}_{mid}_{i}")] for i in range(max(1, num_groups))]
    elif mode == "time":
        num_groups = (len(user_accounts) + 3) // 4
        return [[Button.inline(f"⏳ تحديد وقت مجموعة الحسابات {i+1}", data=f"time_u_{i}")] for i in range(max(1, num_groups))]

@main_bot.on(events.NewMessage(pattern='/start', from_users=OWNER_ID))
async def start(e):
    btns = [
        [Button.inline("🔗 تفاعل يدوي (بوتات)", data="m_bot")],
        [Button.inline("👤 إضافة حساب جديد", data="m_add")],
        [Button.inline("📱 تفاعل يدوي (حسابات)", data="m_user")],
        [Button.inline("📊 الحالة العامة", data="m_stat")],
        [Button.inline("💾 النسخة الاحتياطية للأرقام", data="m_backup")],
        [Button.inline("📤 رفع النسخة الاحتياطية", data="m_restore")],
        [Button.inline("⏱ تحديد وقت التفاعل للأرقام", data="m_time")]
    ]
    await e.respond(f"✅ نظام التفاعل المتطور\n\n🤖 بوتات متصلة: {len(worker_clients)}\n👤 حسابات مضافة: {len(user_accounts)}", buttons=btns)

@main_bot.on(events.NewMessage)
async def on_new_post(e):
    if not e.is_channel or e.sender_id == OWNER_ID: return
    link = get_link(e.chat_id, e.id)
    text = f"📢 منشور جديد في: **{e.chat.title}**\nإختر المجموعة للتفاعل:\n{link}"
    await main_bot.send_message(OWNER_ID, text, buttons=get_group_buttons(e.chat_id, e.id, "bot"), link_preview=False)

@main_bot.on(events.CallbackQuery)
async def on_callback(e):
    if e.sender_id != OWNER_ID: return
    d = e.data.decode()

    if d == "m_bot":
        user_state[e.sender_id] = "link_bot"
        await e.edit("📩 أرسل رابط الرسالة للتفاعل بواسطة البوتات:")
    elif d == "m_user":
        if not user_accounts: return await e.answer("⚠️ لا توجد حسابات مضافة!", alert=True)
        user_state[e.sender_id] = "link_user"
        await e.edit("📩 أرسل رابط الرسالة للتفاعل بواسطة الحسابات:")
    elif d == "m_add":
        user_state[e.sender_id] = "add_p"
        await e.edit("📱 أرسل رقم الهاتف (مثال: +964...):")
    elif d == "m_stat":
        await e.answer(f"🤖 بوتات: {len(worker_clients)}\n👤 حسابات: {len(user_accounts)}", alert=True)
    elif d == "m_backup":
        if user_accounts:
            # كتابة جميع الجلسات الحالية في الملف لضمان إرسال أحدث نسخة
            with open(SESSIONS_FILE, "w") as f:
                for acc in user_accounts:
                    f.write(acc.session.save() + "\n")
        
        if os.path.exists(SESSIONS_FILE) and os.path.getsize(SESSIONS_FILE) > 0:
            await main_bot.send_file(e.chat_id, SESSIONS_FILE, caption="📁 ملف النسخة الاحتياطية للجلسات (الأرقام).\n\nاحتفظ بهذا الملف لرفعه مجدداً عند تشغيل البوت في استضافة جديدة.")
        else:
            await e.answer("⚠️ لا توجد نسخة احتياطية حالياً (لم يتم إضافة أرقام)!", alert=True)
    elif d == "m_restore":
        user_state[e.sender_id] = "upload_backup"
        await e.edit("📤 الرجاء إرسال ملف النسخة الاحتياطية (`sessions.txt`) الآن لرفعه واستعادة الأرقام:")
    elif d == "m_time":
        if not user_accounts: return await e.answer("⚠️ لا توجد حسابات مضافة لتحديد وقتها!", alert=True)
        await e.edit("⏱ إختر المجموعة التي تريد تحديد وقت تفاعلها:", buttons=get_group_buttons(mode="time"))
    elif d.startswith("time_u_"):
        group = d.split("_")[2]
        user_state[e.sender_id] = {"step": "set_time", "group": group}
        await e.edit(f"⏱ أرسل الوقت المطلوب للمجموعة {int(group)+1} (مثال: 10 ثواني، 2 دقيقة)\nالحد المسموح من 10 ثواني إلى 120 دقيقة:")

    elif d.startswith("lst_b_"):
        _, _, chat, mid, group = d.split("_")
        btns = [[Button.inline(emo, data=f"exe_b_{chat}_{mid}_{group}_{emo}") for emo in BOT_EMOJIS[i:i+4]] for i in range(0, len(BOT_EMOJIS), 4)]
        btns.append([Button.inline("⬅️ رجوع", data=f"back_b_{chat}_{mid}")])
        await e.edit(f"🛠 إختر تفاعل لمجموعة البوتات {int(group)+1}:", buttons=btns)

    elif d.startswith("lst_u_"):
        _, _, chat, mid, group = d.split("_")
        btns = [[Button.inline(emo, data=f"exe_u_{chat}_{mid}_{group}_{emo}") for emo in USER_EMOJIS[i:i+4]] for i in range(0, len(USER_EMOJIS), 4)]
        btns.append([Button.inline("⬅️ رجوع", data=f"back_u_{chat}_{mid}")])
        await e.edit(f"🛠 إختر تفاعل لمجموعة الحسابات {int(group)+1}:", buttons=btns)

    elif d.startswith("exe_b_"):
        _, _, chat, mid, group, emo = d.split("_")
        idx = int(group)
        target = worker_clients[idx*4 : (idx+1)*4]
        await e.answer("⏳ جاري التفاعل...")
        tasks = [send_react(w, int(chat) if str(chat).startswith("-100") else chat, int(mid), emo) for w in target]
        await asyncio.gather(*tasks)
        await e.answer(f"✅ تم التفاعل بـ {emo}", alert=True)

    elif d.startswith("exe_u_"):
        _, _, chat, mid, group, emo = d.split("_")
        idx = int(group)
        target = user_accounts[idx*4 : (idx+1)*4]
        delay = group_delays.get(idx, 0)
        
        c_id = int(chat) if str(chat).startswith("-100") else chat
        m_id = int(mid)
        
        if delay > 0:
            async def react_with_delay():
                for u in target:
                    await send_react(u, c_id, m_id, emo)
                    await asyncio.sleep(delay)
            asyncio.create_task(react_with_delay())
            await e.answer(f"⏳ بدأ التفاعل للمجموعة بفاصل {delay} ثانية بين كل حساب!", alert=True)
        else:
            await e.answer("⏳ جاري التفاعل...")
            tasks = [send_react(u, c_id, m_id, emo) for u in target]
            await asyncio.gather(*tasks)
            await e.answer(f"✅ تم التفاعل بـ {emo}", alert=True)

    elif d.startswith("back_b_"):
        _, _, chat, mid = d.split("_")
        await e.edit("إختر المجموعة:", buttons=get_group_buttons(chat, mid, "bot"))
    elif d.startswith("back_u_"):
        _, _, chat, mid = d.split("_")
        await e.edit("إختر المجموعة:", buttons=get_group_buttons(chat, mid, "user"))

@main_bot.on(events.NewMessage(from_users=OWNER_ID))
async def handle_inputs(e):
    state = user_state.get(e.sender_id)
    if not state: return

    if state == "add_p":
        phone = e.text.strip()
        c = TelegramClient(MemorySession(), API_ID, API_HASH)
        await c.connect()
        try:
            h = await c.send_code_request(phone)
            user_state[e.sender_id] = {"step": "add_c", "p": phone, "h": h.phone_code_hash, "c": c}
            await e.respond("📩 أرسل كود التحقق:")
        except Exception as err:
            await e.respond(f"❌ خطأ: {err}"); user_state[e.sender_id] = None

    elif isinstance(state, dict) and state.get("step") == "add_c":
        try:
            cli = state["c"]
            await cli.sign_in(state["p"], e.text, phone_code_hash=state["h"])
            save_session(cli.session.save())
            user_accounts.append(cli)
            await e.respond("✅ تم الدخول بنجاح!"); user_state[e.sender_id] = None
        except SessionPasswordNeededError:
            state["step"] = "add_pw"
            await e.respond("🔐 أرسل كلمة سر التحقق بخطوتين:")
        except Exception as err: await e.respond(f"❌ خطأ: {err}")

    elif isinstance(state, dict) and state.get("step") == "add_pw":
        try:
            cli = state["c"]
            await cli.sign_in(password=e.text)
            save_session(cli.session.save())
            user_accounts.append(cli)
            await e.respond("✅ تم الحساب بنجاح!"); user_state[e.sender_id] = None
        except Exception as err: await e.respond(f"❌ خطأ: {err}")

    elif state == "link_bot":
        c, m = parse_link(e.text)
        if c:
            user_state[e.sender_id] = None
            await e.respond(f"إختر المجموعة للبوتات:\n{e.text}", buttons=get_group_buttons(c, m, "bot"), link_preview=False)

    elif state == "link_user":
        c, m = parse_link(e.text)
        if c:
            user_state[e.sender_id] = None
            await e.respond(f"إختر المجموعة للحسابات:\n{e.text}", buttons=get_group_buttons(c, m, "user"), link_preview=False)

    elif isinstance(state, dict) and state.get("step") == "set_time":
        text = e.text.strip()
        num = re.search(r'\d+', text)
        if num:
            val = int(num.group())
            if "دقيق" in text or "m" in text.lower():
                val *= 60
            
            if 10 <= val <= 7200:
                group_idx = int(state["group"])
                group_delays[group_idx] = val
                user_state[e.sender_id] = None
                await e.respond(f"✅ تم تعيين الوقت للمجموعة {group_idx + 1} ليكون فاصلاً زمنياً بـ {val} ثانية بين تفاعل كل حساب.")
            else:
                await e.respond("❌ الوقت غير صالح. الرجاء إدخال وقت بين 10 ثواني و 120 دقيقة:")
        else:
            await e.respond("❌ الرجاء كتابة الرقم مع الوحدة (مثال: 10 ثواني):")

    elif state == "upload_backup":
        if e.document:
            await main_bot.download_media(e.document, file=SESSIONS_FILE)
            user_state[e.sender_id] = None
            for acc in user_accounts:
                try:
                    await acc.disconnect()
                except:
                    pass
            user_accounts.clear()
            await init_accounts()
            await e.respond(f"✅ تم استلام النسخة الاحتياطية بنجاح!\nعدد الحسابات المضافة الآن: {len(user_accounts)}")
        else:
            await e.respond("❌ الرجاء إرسال الملف كمستند (File)، وليس كنص عادي.")

async def main():
    await main_bot.start(bot_token=BOT_TOKEN)
    async def sw(t):
        try:
            cl = TelegramClient(MemorySession(), API_ID, API_HASH)
            await cl.start(bot_token=t); worker_clients.append(cl)
        except: pass
    await asyncio.gather(*[sw(t) for t in WORKER_TOKENS])
    await init_accounts()
    print("🚀 System Online.")
    await main_bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
