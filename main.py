# handle_voice_selection function ထဲက try block ကို ဒီကုဒ်နဲ့ လဲလိုက်ပါ

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # အသံထုတ်ယူမယ့် အပိုင်းကို အသစ်ပြန်ပြင်ထားပါတယ်
        response = model.generate_content(
            contents=text,
            generation_config={
                "response_mime_type": "audio/mp3",
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_id": voice_id
                    }
                }
            }
        )

        # Audio content ကို ဆွဲထုတ်ခြင်း
        if hasattr(response, 'audio_contents') and response.audio_contents:
            audio_data = response.audio_contents[0].data
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "gemini_voice.mp3"
            await query.message.reply_audio(audio=audio_file, caption=f"🎙 Gemini Voice: {voice_display_name}")
            await msg.delete()
        else:
            await query.edit_message_text("Error: Gemini API ကနေ အသံဒေတာ မရရှိပါဘူး။ (Quota ပြည့်နေတာ ဒါမှမဟုတ် Region ကန့်သတ်ချက် ဖြစ်နိုင်ပါတယ်)")
