import aiosqlite

# تعریف متغیر های سراسری برای راحتی در استفاده های تکراری.
DB_NAME = 'db.db'
TABLE_USERS = 'tbl_users'

# فانکشن ایسینک برای پیدا کردن ویا درست کردن یک یوزر بر اساس چت آی دی.
# در ابزار هایی مانند ربات تلگرام که نیاز هست چندین درخواست همزمان اجرا بشه از فانکشن های ایسینک استفاده میکنیم.
async def get_or_create_user(chat_id: str, dest_lang: str = 'en', src_lang: str = 'fa'):

    # با استفاده از متد (with) یک کانکشن به دیتابیس میسازیم بنام (db) و از این پس توی بلوک (with) با صدا زدن این نام کانکشن فراخوانی میشه.
    async with aiosqlite.connect(DB_NAME) as db:

        # کوئری ست ها دستور های سطح دیتابیس ما هستن که با زبان sql نوشته میشن.
        # در این کوئری ست ما به دنبال رکوردی در دیتابیست و تیبل یوزر ها میگردیم که فیلد (chat_id) برابر با پارامتر چت آی دی ورودی فانکشن باشه.
        query_set = await db.execute(
            f'SELECT chat_id, dest_lang, src_lang FROM {TABLE_USERS} WHERE chat_id = ?',
            (chat_id,)
        )

        # چون فیلد چت آی دی یونیک هست نمیشه چند رکورد مقدار یکسان داشته باشیم پس با فاکنشن fetchone نخستین رکورد کوئری ستمون رو دریافت میکنیم.
        row = await query_set.fetchone()

        # اگر رکوردی وجود داشت مقدار های (chat_id, dest_lang, src_lang) رو بر اساس آیتم های row که مشخصه های یوزر دریافت شده اس دیتابیس هسن بازنویسی میکنیم.
        if row:
            chat_id, dest_lang, src_lang = row

        # اگر هیچ دیتایی در row نبود نشان بر یافت نشدن یوزر هست پس یک کوئری ست برای ساخت یوزر تازه اجرا میکنیم.
        else:
            await db.execute(
                f'INSERT INTO {TABLE_USERS} (chat_id, dest_lang, src_lang) VALUES (?, ?, ?)',
                (chat_id, dest_lang, src_lang)
            )

            # پس از اجرای فانکشن کامیت کوئری ست رکورد رو در دیتابیس میسازه.
            await db.commit()


        # در نهایت نتیجه ای بازگردانی میکنیم که قالب دیکشنری داره و سه پارامتر مورد نیاز رو باز میگردونه.
        return {
            'chat_id': chat_id,
            'dest_lang': dest_lang,
            'src_lang': src_lang
        }
    

# یک فانکشن برای ویرایش زبان های هر کاربر داریم به جز کامند سطح sql تفاوتی با فانکشن بالا نداره.
async def update_user_langs(chat_id: str, dest_lang: str, src_lang: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            f'UPDATE {TABLE_USERS} SET dest_lang = ?, src_lang = ? WHERE chat_id = ?',
            (dest_lang, src_lang, chat_id)
        )
        
        await db.commit()

        # پس از اجرای دستور ویرایش در سطح دیتابیس با استفاده از فانکشن دریافت یوزر یوزرمون رو از دیتابیس میگیریم.
        # در اصل فانکشن get_or_create_user اجرا میشه و نتیجه ی اون ریترن میشه.
        # این کار برای پیش گیری از نوشتن کد تکراری انجام شد.
        return await get_or_create_user(chat_id)