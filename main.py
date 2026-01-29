from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters, ApplicationBuilder, MessageHandler, ContextTypes, CommandHandler, CallbackQueryHandler
from googletrans import Translator
from db import get_or_create_user, update_user_langs


TOKEN = ''
trans = Translator()



def language_keyboard(prefix: str):
    LANGUAGES = {
        "fa": "Parsi",
        "en": "English",
        "de": "Deutsch",
    }
    # دکمه ها در ربات تلگرام برابر با یک لیست از کلاس InlineKeyboardButton که مقدار دهی شده است میباشند.
    keyboard = []

    # از دیکشنری زبان ها نام و کد زبان جدا میکنیم و در یک لوپ مقدار دهی کیبورد را انجام میدهیم.
    for code, name in LANGUAGES.items():
        # افزودن یک دکمه به لیست مربوط به کیبورد.
        keyboard.append([
            # هر دکمه یک نام نمایشی و یک کالبک دیتا برای مشخص بودن نتیجه پس از انتخاب دارد.
            # الگوی نمونه کالبک دیتای ما به این صورت میشود در نهایت :‌ src:fa 
            InlineKeyboardButton(name, callback_data=f"{prefix}:{code}")
        ])

    # پس از ساخت لیست دکمه ها یک کلاس جمع بندی شده از کیبورد باز میگردانیم.
    return InlineKeyboardMarkup(keyboard)


def main_menu():
    keyboard = [
        [InlineKeyboardButton("Update langs", callback_data="update_lang")]
    ]
    return InlineKeyboardMarkup(keyboard)


# این تابع زمانی اجرا می‌شود که کاربر روی یکی از دکمه‌های شیشه‌ای (InlineKeyboard) کلیک کند
# در این حالت، تلگرام به جای ارسال پیام جدید، یک CallbackQuery برای ربات می‌فرستد
# به همین دلیل از update.callback_query استفاده می‌کنیم، نه update.message
async def update_languages(update: Update, context):
    query = update.callback_query # اطلاعات کلیک کاربر روی دکمه
    await query.answer() # اعلام به تلگرام که کلیک دریافت شده (برای جلوگیری از loading)

    # دیتا برابر با کالبک دیتای هر دکمه ی انتخاب شده میباشد.
    data = query.data

    # اگر کالبک دیتا update_lang بود یعنی کاربر این دکمه را انتخاب کرده است بنابر این دکمه ها برای انتخاب زبان نخست آماده سازی میشوند.
    if data == "update_lang":
        context.user_data.clear()
        await query.message.edit_text(
            "میخوای از چه زبونی برات ترجمه کنم ؟؟؟",
            reply_markup=language_keyboard("src")
        )

    # هنگامی که دیتای ما با src شروع شود نشان بر این است که زبان نخست انتخاب شده است بنابر این ادامه میدهیم برای انتخاب زبان دوم.
    elif data.startswith("src:"):
        # با شروع فرآیند انتخاب زبان، وضعیت قبلی کاربر پاک می‌شود
        src_lang = data.split(":")[1]

        # context.user_data یک دیکشنری مخصوص هر کاربر است
        # که تا پایان تعامل کاربر با ربات باقی می‌ماند
        # از آن برای نگهداری وضعیت (state) مثل زبان انتخاب‌شده استفاده می‌کنیم
        context.user_data["src"] = src_lang

        await query.message.edit_text(
            "میخوام به چه زبونی برات ترجمه کنم ؟؟؟",
            reply_markup=language_keyboard("dst")
        )

    # هنگامیکه دیتا با dst  شروع شود نشان بر این است که زبان دوم هم انتخاب شده است بنابر این ثبت در دیتابیس را انجام میدهیم.
    elif data.startswith("dst:"):
        dst_lang = data.split(":")[1]
        context.user_data["dst"] = dst_lang

        src = context.user_data["src"]
        dst = context.user_data["dst"]

        result = await update_user_langs(query.from_user.id, dest_lang=dst, src_lang=src)
        await query.message.edit_text(f'زبان های شما ویرایش شدن.\n {result}')



# یک فانکشن ایسینگ برای دریافت پیام کاربر و ترجمه
async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):

    #  دریافت مشخصه های کاربر از دیتابیس برای استفاده از زبان های مشخص شده.
    user_detail = await get_or_create_user(update.message.chat.id)
    # دریافت پیام کاربر
    message_text = update.message.text

    result = await trans.translate(
        message_text,
        dest = user_detail.get('dest_lang', 'en'), # با توجه بر اینکه میدونیم user_detail یک دیکشنری است که فانکشن get_or_create_user برای ما فرستاده با استفاده از متد get میتونیم یک key مشخص کنیم که مقدارش دریافت بشه و اگر این کلید به هر دلیل وجود نداشت برای پیش گیری از خطای نرم افزاری مقدار پیش فرض en قرار بدیم.
        src = user_detail.get('src_lang', 'fa')
    )

    # مقدار تکست نتیجه ی ترجمه رو با استفاده از فانکشن reply_text برای همون کاربر درخواست کننده میفرستیم.
    await update.message.reply_text(result.text)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فانکشن استارت پس از شروع ربات برای هر کاربر یک یوزر در دیتابیس درست میکنه.
    result = await get_or_create_user(update.message.chat.id)
    await update.message.reply_text('به ربات دینا خوش اومدی', reply_markup=main_menu())


# فانشکن اصلی که با اجرای اسکریپتمون اجرا میشه و کنترل کامل رباتمون رو انجام میده.
def main():
    # پیش از هر چیز یک اپلیکیشم میسازیم و با استفاده از توکن به رباتمون وصل میکنیم.
    app = ApplicationBuilder().token(TOKEN).build()

    # هر هندلر بر اساس پیامی که دریافت میکنه و فیلتر هایی که ما مشخص کردیم یک فانکشن اجرا میکنه.
    app.add_handler(
        CommandHandler('start', start)
    )

    app.add_handler(
        CommandHandler('langs', start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND, translate
        )
    )

    app.add_handler(CallbackQueryHandler(update_languages))

    app.run_polling()

if __name__ == '__main__':
    main()