# ربات تلگرامی تولید لینک دانلود استریم

این ربات تلگرامی فایل‌های ارسالی کاربران را دریافت کرده و بدون ذخیره کردن آن‌ها روی سرور، لینک دانلود استریم تولید می‌کند.

**نسخه جدید با FastAPI/Uvicorn به جای Flask**

## ویژگی‌ها

- ✅ پشتیبانی از تمام فرمت‌های فایل تلگرام (سند، ویدیو، صدا، عکس، انیمیشن و...)
- ✅ بدون ذخیره فایل روی سرور - استریم مستقیم از سرورهای تلگرام
- ✅ رابط کاربری فارسی
- ✅ نمایش مشخصات فایل قبل از تولید لینک
- ✅ امکان لغو عملیات
- ✅ توکن‌های امن یک‌بارمصرف با زمان انقضا
- ✅ پشتیبانی از Range Request برای دانلود قابل ادامه
- ✅ دیتابیس SQLite برای ذخیره موقت اطلاعات

## پیش‌نیازها

- Python 3.8+
- Node.js 16+ (برای بیلد صفحه React)

## نصب

### 1. نصب وابستگی‌های Python:

```bash
pip install -r requirements.txt
```

### 2. نصب وابستگی‌های React و بیلد صفحه تبلیغاتی:

```bash
cd ad-page
npm install
npm run build
cd ..
```

## تنظیمات

قبل از اجرای ربات، باید متغیرهای محیطی را تنظیم کنید:

```bash
cp .env.example .env
```

سپس فایل `.env` را ویرایش کرده و مقادیر زیر را تنظیم کنید:

```bash
BOT_TOKEN="YOUR_BOT_TOKEN_HERE"
SERVER_DOMAIN="https://your-domain.com"
SERVER_PORT="8000"
DATABASE_PATH="./bot_data.db"
TOKEN_EXPIRATION="3600"
SECRET_KEY="your-secret-key-change-in-production"
```

### توضیحات متغیرها:

- `BOT_TOKEN`: توکن ربات تلگرام که از [@BotFather](https://t.me/BotFather) دریافت می‌کنید
- `SERVER_DOMAIN`: دامنه عمومی سرور شما که کاربران به آن دسترسی دارند (مثلاً `https://example.com`)
- `SERVER_PORT`: پورتی که سرور FastAPI روی آن اجرا می‌شود (پیش‌فرض: 8000)
- `DATABASE_PATH`: مسیر فایل دیتابیس SQLite
- `TOKEN_EXPIRATION`: زمان انقضای توکن‌ها به ثانیه (پیش‌فرض: 3600 = 1 ساعت)
- `SECRET_KEY`: کلید مخفی برای تولید توکن‌های امن

## نحوه استفاده

1. **دریافت توکن ربات:**
   - به [@BotFather](https://t.me/BotFather) در تلگرام مراجعه کنید
   - دستور `/newbot` را ارسال کنید
   - نام و نام کاربری ربات خود را وارد کنید
   - توکن دریافت شده را کپی کنید

2. **تنظیم متغیرهای محیطی:**
   ```bash
   export BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
   export SERVER_DOMAIN="https://your-domain.com"
   ```

3. **بیلد کردن صفحه تبلیغاتی (React App):**
   ```bash
   cd ad-page
   npm install
   npm run build
   cd ..
   ```

4. **اجرای ربات:**
   ```bash
   python telegram_stream_bot.py
   ```

   یا با uvicorn مستقیم:
   ```bash
   uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
   ```

## نحوه کار ربات

1. کاربر ربات را با دستور `/start` شروع می‌کند و پیام خوش‌آمدگویی دریافت می‌کند
2. کاربر فایل مورد نظر را برای ربات ارسال می‌کند
3. ربات مشخصات فایل (نام، نوع، حجم) را نمایش داده و دو گزینه ارائه می‌دهد:
   - 🔗 تولید لینک دانلود
   - ❌ لغو
4. اگر کاربر "تولید لینک دانلود" را انتخاب کند:
   - ربات یک توکن امن و یک‌بارمصرف تولید می‌کند
   - لینک صفحه واسط تبلیغاتی را ارسال می‌کند
   - کاربر می‌تواند با کلیک روی لینک به صفحه واسط برود
5. در صفحه واسط:
   - شمارش معکوس 15 ثانیه‌ای نمایش داده می‌شود
   - بعد از پایان شمارش، دکمه "تولید لینک دانلود" فعال می‌شود
   - با کلیک روی دکمه، دانلود فایل شروع می‌شود
6. اگر کاربر "لغو" را انتخاب کند:
   - عملیات کنسل شده و توکن حذف می‌شود

## ساختار لینک استریم

لینک‌های تولید شده به این شکل هستند:
```
https://your-domain.com/download?token={secure_token}
```

وقتی کاربر روی این لینک کلیک می‌کند:
1. درخواست به سرور FastAPI ارسال می‌شود
2. توکن اعتبارسنجی می‌شود (یک‌بارمصرف، دارای زمان انقضا)
3. صفحه واسط تبلیغاتی با اطلاعات فایل نمایش داده می‌شود
4. بعد از 15 ثانیه، کاربر می‌تواند دانلود را شروع کند
5. فایل از سرورهای تلگرام استریم شده و روی سرور ذخیره نمی‌شود

## نکات مهم

- ⚠️ سرور FastAPI باید از طریق اینترنت قابل دسترسی باشد
- ⚠️ برای تولید محیطی، از یک وب‌سرور مانند Nginx به عنوان reverse proxy استفاده کنید
- ⚠️ فایل‌ها فقط تا زمانی که توکن معتبر است در دسترس هستند
- ⚠️ هر توکن فقط یک‌بار قابل استفاده است
- ⚠️ توکن‌ها بعد از زمان انقضا (پیش‌فرض 1 ساعت) غیرفعال می‌شوند

## مثال استفاده از Nginx به عنوان Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## ساختار پروژه

```
/workspace/
├── telegram_stream_bot.py    # فایل اصلی ربات
├── fastapi_app.py            # برنامه FastAPI
├── config.py                 # تنظیمات
├── database.py               # مدل‌های دیتابیس SQLite
├── telegram_service.py       # سرویس‌های تلگرام
├── requirements.txt          # وابستگی‌های Python
├── .env.example              # نمونه فایل تنظیمات
└── ad-page/                  # صفحه تبلیغاتی React
    ├── src/
    │   └── App.jsx
    ├── public/
    └── dist/                 # خروجی بیلد
```

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.
