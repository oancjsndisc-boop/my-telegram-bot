from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import timezone, timedelta
from flask import Flask
import threading
import os

# --- إعداد Flask لإبقاء البوت حياً ---
app = Flask('')
@app.route('/')
def home():
    return "I am alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

# ====== الإعدادات ======
TOKEN = "8473988184:AAE7gxv4Mb2tJDdANbxOpWUfi8ukPYfzq4Q"
GROUP_ID = -1002940184456 
IRAQ_TZ = timezone(timedelta(hours=3))

bot_data = {
    "videos": [],
    "last_message_id": None,
    "scheduler": AsyncIOScheduler(timezone=IRAQ_TZ),
    "is_running": False
}

async def post_video_task(context: ContextTypes.DEFAULT_TYPE):
    if not bot_data["videos"]:
        return
    video_id = bot_data["videos"].pop(0)
    if bot_data["last_message_id"]:
        try:
            await context.bot.delete_message(chat_id=GROUP_ID, message_id=bot_data["last_message_id"])
        except:
            pass
    try:
        msg = await context.bot.send_video(chat_id=GROUP_ID, video=video_id)
        bot_data["last_message_id"] = msg.message_id
        bot_data["videos"].append(video_id)
    except Exception as e:
        print(f"Error: {e}")

async def start_posting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_data["videos"]:
        await update.message.reply_text("❌ القائمة فارغة! أرسل المقاطع للبوت.")
        return
    if bot_data["is_running"]:
        await update.message.reply_text("⚠️ البوت يعمل بالفعل.")
        return
    bot_data["is_running"] = True
    if not bot_data["scheduler"].running:
        bot_data["scheduler"].start()
    bot_data["scheduler"].add_job(post_video_task, "interval", minutes=2, args=[context], id="posting_job", replace_existing=True)
    await post_video_task(context)
    await update.message.reply_text("🚀 بدأ النشر التلقائي.")

async def handle_private_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type == 'private' and update.message.video:
        video_id = update.message.video.file_id
        bot_data["videos"].append(video_id)
        await update.message.reply_text(f"✅ تم حفظ المقطع. العدد: {len(bot_data['videos'])}")

async def stop_posting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if bot_data["is_running"]:
        bot_data["scheduler"].remove_job("posting_job")
        bot_data["is_running"] = False
        await update.message.reply_text("🛑 تم إيقاف النشر.")

def main():
    # تشغيل Flask في خيط (Thread) منفصل
    threading.Thread(target=run_flask).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start_posting", start_posting))
    app.add_handler(CommandHandler("stop_posting", stop_posting))
    app.add_handler(MessageHandler(filters.VIDEO, handle_private_videos))

    print("✅ البوت يعمل..")
    app.run_polling()

if __name__ == "__main__":
    main()
    
