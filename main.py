import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler
import edge_tts

# --- CONFIGURATION ---
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@reeac_99" # မင်းရဲ့ Channel ID

# Flask Server for Render
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"
def run(): app.run(host='0.0.0.0', port=10000)

# Conversation States
JOIN_CHECK, GET_TEXT, SELECT_VOICE = range(3)

# Creator တွေ အသုံးများတဲ့ အသံ ၁၀ မျိုး (Female 4, Male 6)
VOICES = {
    # --- Female Voices (၄ သံ) ---
    "Nilar (MM-Female)": "my-MM-NilarNeural",
    "Ava (EN-Female)": "en-US-AvaNeural",
    "Emma (EN-Female)": "en-US-EmmaNeural",
    "Sonia (EN-Female)": "en-GB-SoniaNeural",
    
    # --- Male Voices (၆ သံ) ---
    "Thiha (MM-Male)": "my-MM-ThihaNeural",
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
            await update.message.reply_text("ရှေ့ဆက်ဖို့ ကျွန်ုပ်တို့၏ Channel ကို အရင် Join ပေးပါ။", reply_markup=InlineKeyboardMarkup(keyboard))
            return JOIN_CHECK
        
        await update.message.reply_text("မင်္ဂလာပါ! အသံပြောင်းလိုသော စာသားကို ရိုက်ထည့်ပေးပါ။")
        return GET_TEXT
    except Exception:
        await update.message.reply_text("Error: Channel ID မှားနေပါသလား သို့မဟုတ် Bot ကို Admin မခန့်ရသေးပါ။")
        return ConversationHandler.END

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status not in ['left', 'kicked']:
            await query.message.delete() # Join ပြီးတာနဲ့ စာဟောင်းဖျက်မယ်
            await context.bot.send_message(chat_id=user_id, text="ကျေးဇူးတင်ပါတယ်။ အခု အသံပြောင်းလိုတဲ့ စာသားကို ရိုက်ထည့်ပါ။")
            return GET_TEXT
        else:
            await query.message.reply_text("Join မလုပ်ရသေးပါ။ ကျေးဇူးပြု၍ အရင် Join ပါ။")
            return JOIN_CHECK
    except:
        return JOIN_CHECK

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['text_to_convert'] = update.message.text
    # Button တွေကို ၂ ခုတစ်တွဲစီ ပြပေးမယ်
    keyboard = []
    v_keys = list(VOICES.keys())
    for i in range(0, len(v_keys), 2):
        row = [InlineKeyboardButton(v_keys[i], callback_data=v_keys[i])]
        if i+1 < len(v_keys):
            row.append(InlineKeyboardButton(v_keys[i+1], callback_data=v_keys[i+1]))
        keyboard.append(row)
        
    await update.message.reply_text("အသုံးပြုလိုသော အသံကို ရွေးချယ်ပေးပါ (Female 4 / Male 6) -", reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECT_VOICE

async def handle_voice_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    voice_name = query.data
    text = context.user_data.get('text_to_convert')
    await query.answer()
    
    msg = await query.edit_message_text(f"⏳ {voice_name} အသံဖြင့် ပြောင်းလဲနေပါသည်...")
    
    try:
        output_file = f"voice_{query.from_user.id}.mp3"
        communicate = edge_tts.Communicate(text, VOICES[voice_name])
        await communicate.save(output_file)
        
        await query.message.reply_audio(audio=open(output_file, 'rb'), caption=f"🎙 Voice: {voice_name}")
        await msg.delete()
        os.remove(output_file)
    except Exception as e:
        await query.edit_message_text(f"Error: {str(e)}")
    
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
    # drop_pending_updates က Conflict ဖြစ်နေတဲ့ စာဟောင်းတွေကို အကုန်ရှင်းပေးမယ်
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
