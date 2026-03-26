import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
import edge_tts

# --- CONFIGURATION ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@reeac_99"

app = Flask('')
@app.route('/')
def home(): return "Bot is Online"
def run(): app.run(host='0.0.0.0', port=10000)

JOIN_CHECK, GET_TEXT, SELECT_VOICE = range(3)

# Creator Voices (သေချာခွဲပေးထားတယ်)
VOICES = {
    "Nilar (MM-Female)": "my-MM-NilarNeural",
    "Thiha (MM-Male)": "my-MM-ThihaNeural",
    "Ava (EN-Female)": "en-US-AvaNeural",
    "Emma (EN-Female)": "en-US-EmmaNeural",
    "Sonia (EN-Female)": "en-GB-SoniaNeural",
    "Guy (EN-Male)": "en-US-GuyNeural",
    "Andrew (EN-Male)": "en-US-AndrewNeural",
    "Brian (EN-Male)": "en-US-BrianNeural",
    "Ryan (EN-Male)": "en-GB-RyanNeural",
    "Alfie (EN-Male)": "en-GB-AlfieNeural"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['left', 'kicked']:
            keyboard = [[InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")],
                        [InlineKeyboardButton("I have joined ✅", callback_data="check_join")]]
            await update.message.reply_text("ရှေ့ဆက်ဖို့ Channel အရင် Join ပေးပါ။", reply_markup=InlineKeyboardMarkup(keyboard))
            return JOIN_CHECK
        await update.message.reply_text("အသံပြောင်းလိုသော စာသားကို ရိုက်ထည့်ပေးပါ။")
        return GET_TEXT
    except:
        await update.message.reply_text("Bot ကို Channel မှာ Admin အရင်ခန့်ပေးပါ။")
        return ConversationHandler.END

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=query.from_user.id)
    if member.status not in ['left', 'kicked']:
        await query.message.delete()
        await context.bot.send_message(chat_id=query.from_user.id, text="စာသားကို ရိုက်ထည့်နိုင်ပါပြီ။")
        return GET_TEXT
    return JOIN_CHECK

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['text_to_convert'] = update.message.text
    keyboard = []
    v_keys = list(VOICES.keys())
    for i in range(0, len(v_keys), 2):
        row = [InlineKeyboardButton(v_keys[i], callback_data=v_keys[i])]
        if i+1 < len(v_keys): row.append(InlineKeyboardButton(v_keys[i+1], callback_data=v_keys[i+1]))
        keyboard.append(row)
    await update.message.reply_text("အသုံးပြုလိုသော အသံကို ရွေးချယ်ပါ -", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_VOICE

async def handle_voice_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    voice_name = query.data
    text = context.user_data.get('text_to_convert')
    await query.answer()
    
    msg = await query.edit_message_text("⏳ အသံဖိုင် ပြောင်းလဲနေသည်...")
    
    try:
        # စာသားထဲမှာ မြန်မာစာပါရင် မြန်မာသံကို အတင်းပြောင်းခိုင်းမယ်
        selected_voice = VOICES[voice_name]
        has_burmese = any('\u1000' <= char <= '\u109F' for char in text)
        
        if has_burmese and "MM" not in voice_name:
            # မြန်မာစာကို အင်္ဂလိပ်သံနဲ့ဖတ်ရင် Error တက်တတ်လို့ Auto-Switch လုပ်ပေးတာ
            selected_voice = "my-MM-NilarNeural" if "Female" in voice_name else "my-MM-ThihaNeural"

        output_file = f"voice_{query.from_user.id}.mp3"
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(output_file)
        
        await query.message.reply_audio(audio=open(output_file, 'rb'), caption=f"🎙 Voice: {voice_name}")
        await msg.delete()
        os.remove(output_file)
    except Exception as e:
        await query.edit_message_text(f"Error: {str(e)}\n(မြန်မာစာကို မြန်မာသံနဲ့ပဲ စမ်းကြည့်ပါ)")
    
    return GET_TEXT

def main():
    Thread(target=run).start()
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            JOIN_CHECK: [CallbackQueryHandler(check_join_callback, pattern="^check_join$")],
            GET_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            SELECT_VOICE: [CallbackQueryHandler(handle_voice_selection)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    application.add_handler(conv_handler)
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
