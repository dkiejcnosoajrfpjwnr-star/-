import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot, ReactionTypeEmoji
from telegram.ext import Application, ContextTypes, MessageHandler, CallbackQueryHandler, CommandHandler, filters
from telegram.error import BadRequest

# Configuration
MAIN_TOKEN = "8324182409:AAGupTeJHB-pZvegVcuWEm6f4_QXOG-KFGA"
WORKER_TOKENS = [
    "8339241896:AAH7Ooe4jaVUGQRj5CP-C6HEeLBU4OngQAU",
    "8246715327:AAFUD6M3JnjnjMhceJV8195HaIkhOJnL88Q",
    "8358087517:AAHDBidKo4m4njVfkv6rOxbsw6vDqLaojhM",
    "8393831841:AAEkK2M_TRJhmkBAgBTyRjhNPLRdbERtjck"
]
ALL_TOKENS = [MAIN_TOKEN] + WORKER_TOKENS
ADMIN_ID = 6668195885

# Reactions
REACTIONS = ["😭", "❤️‍🔥", "🕊️", "👏🏻", "💯"]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow admin to start interaction in private
    if update.effective_user.id != ADMIN_ID:
        return
        
    await update.message.reply_text(
        f"مرحبًا عزيزي {update.effective_user.first_name}\n"
        "أنا بوت تفاعل بالرموز التعبيرية 🤖\n"
        "يمكنك إضافتي إلى قناة أو كروب، وسأساعدك على التفاعل مع الرسائل الجديدة بسهولة."
    )

async def handle_new_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore messages from private chats or if not from channels/groups
    if update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    
    # Send notification to Admin Private Chat
    try:
        # 1. Send text prompting for reaction
        await context.bot.send_message(chat_id=ADMIN_ID, text="ماذا تريد أن تتفاعل على هذه الرسالة؟")
        
        # 2. Copy the content (text/media) to admin
        # Prepare buttons
        keyboard = [
            [InlineKeyboardButton(emoji, callback_data=f"react|{chat_id}|{message_id}|{emoji}") for emoji in REACTIONS]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.copy_message(
            chat_id=ADMIN_ID,
            from_chat_id=chat_id,
            message_id=message_id,
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logging.error(f"Error forwarding message from {chat_id}: {e}")

async def handle_reaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    if len(data) != 4 or data[0] != "react":
        return

    chat_id = int(data[1])
    message_id = int(data[2])
    emoji = data[3]
    
    # Execute reactions with all bots
    tasks = []
    for token in ALL_TOKENS:
        tasks.append(react_with_bot(token, chat_id, message_id, emoji))
    
    results = await asyncio.gather(*tasks)
    success_count = results.count(True)
    
    # Remove buttons from the message in private chat to indicate done
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logging.warning(f"Could not remove buttons: {e}")
        
    # Send confirmation
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"✅ تم التفاعل على رسالتك بنجاح")

async def react_with_bot(token, chat_id, message_id, emoji):
    try:
        async with Bot(token) as bot:
            await bot.set_message_reaction(
                chat_id=chat_id,
                message_id=message_id,
                reaction=[ReactionTypeEmoji(emoji)]
            )
        return True
    except Exception as e:
        logging.error(f"Failed to react with token ...{token[-5:]}: {e}")
        return False

def main():
    application = Application.builder().token(MAIN_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    
    # Handle posts in Channels and Groups
    # filters.ChatType.PRIVATE is excluded.
    # We want everything else.
    application.add_handler(MessageHandler(~filters.ChatType.PRIVATE, handle_new_message))
    
    application.add_handler(CallbackQueryHandler(handle_reaction_callback))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
