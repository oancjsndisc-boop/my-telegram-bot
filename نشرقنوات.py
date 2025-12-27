from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import timezone, timedelta

# ====== الإعدادات ======
TOKEN = "8473988184:AAE7gxv4Mb2tJDdANbxOpWUfi8ukPYfzq4Q"
GROUP_ID = -1002940184456  # أيدي الكروب الذي سيتم النشر فيه
IRAQ_TZ = timezone(timedelta(hours=3))

# تخزين البيانات
bot_data = {
    "videos": [],
    "last_message_id": None,
    "scheduler": AsyncIOScheduler(timezone=IRAQ_TZ),
    "is_running": False
}

# ====== وظيفة النشر ======
async def post_video_task(context: ContextTypes.DEFAULT_TYPE):
    if not bot_data["videos"]:
        return

    # سحب أول فيديو في القائمة
    video_id = bot_data["videos"].pop(0)

    # حذف الفيديو القديم من الكروب
    if bot_data["last_message_id"]:
        try:
            await context.bot.delete_message(chat_id=GROUP_ID, message_id=bot_data["last_message_id"])
        except:
            pass

    # إرسال الفيديو الجديد للكروب
    try:
        msg = await context.bot.send_video(chat_id=GROUP_ID, video=video_id)
        bot_data["last_message_id"] = msg.message_id
        # إعادة إضافة الفيديو لنهاية القائمة (ليكون النشر دوري)
        bot_data["videos"].append(video_id)
    except Exception as e:
        print(f"Error: {e}")

# ====== أمر بدء النشر ======
async def start_posting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_data["videos"]:
        await update.message.reply_text("❌ القائمة فارغة! أرسل المقاطع للبوت في الخاص أولاً.")
        return

    if bot_data["is_running"]:
        await update.message.reply_text("⚠️ البوت يعمل بالفعل ويقوم بالنشر كل دقيقتين.")
        return

    bot_data["is_running"] = True
    
    # بدء المجدول إذا لم يكن يعمل
    if not bot_data["scheduler"].running:
        bot_data["scheduler"].start()

    # إضافة وظيفة النشر كل دقيقتين
    bot_data["scheduler"].add_job(
        post_video_task,
        "interval",
        minutes=2,
        args=[context],
        id="posting_job",
        replace_existing=True
    )

    # إرسال أول فيديو فوراً عند كتابة الأمر
    await post_video_task(context)
    await update.message.reply_text("🚀 تم بدء النشر التلقائي في الكروب (فيديو كل 2 دقيقة).")

# ====== استقبال الفيديوهات في الخاص ======
async def handle_private_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # التأكد أن الرسالة في الخاص وليس في الكروب
    if update.message.chat.type == 'private':
        if update.message.video:
            video_id = update.message.video.file_id
            bot_data["videos"].append(video_id)
            await update.message.reply_text(f"✅ تم حفظ المقطع بنجاح. العدد الحالي في القائمة: {len(bot_data['videos'])}")

# ====== أمر التوقف ======
async def stop_posting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if bot_data["is_running"]:
        bot_data["scheduler"].remove_job("posting_job")
        bot_data["is_running"] = False
        await update.message.reply_text("🛑 تم إيقاف النشر التلقائي.")
    else:
        await update.message.reply_text("⚠️ النشر متوقف بالفعل.")

# ====== التشغيل ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # الأوامر
    app.add_handler(CommandHandler("start_posting", start_posting))
    app.add_handler(CommandHandler("stop_posting", stop_posting))
    
    # استقبال الفيديوهات
    app.add_handler(MessageHandler(filters.VIDEO, handle_private_videos))

    print("✅ البوت يعمل.. أرسل المقاطع في الخاص ثم اكتب /start_posting")
    app.run_polling()

if __name__ == "__main__":
    main()
