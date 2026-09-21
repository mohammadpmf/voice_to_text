# Voice to Text - تبدیل گفتار فارسی به متن

برنامه دسکتاپ برای تبدیل صحبت میکروفون به متن فارسی و انگلیسی با Faster-Whisper
به صورت کاملا محلی و آفلاین، با رابط گرافیکی مدرن PySide6 و تم تاریک پیش فرض.

## امکانات

- ضبط از میکروفون با انتخاب دستگاه
- نمایشگر زنده سطح صدا (VU Meter) برای اطمینان از درست بودن میکروفون
- تبدیل خودکار به متن فارسی و انگلیسی
- انتخاب مدل Whisper: tiny / base / small / medium / large-v3
- استفاده خودکار از GPU در صورت وجود، در غیر این صورت CPU
- دانلود یکباره مدل و استفاده همیشگی بدون اینترنت
- عدم Freeze رابط کاربری با Thread جداگانه برای ضبط و ترنسکرایب
- افزودن متن جدید به متن قبلی
- Copy All / Clear / Save TXT
- حالت تاریک پیش فرض و امکان تغییر به حالت روشن
- کلیدهای میانبر: Ctrl+Shift+Space برای شروع و توقف، Ctrl+S برای ذخیره، Ctrl+L برای پاک کردن
- معماری Provider-based: Local / OpenAI API / Google Cloud Speech به صورت اختیاری
- بدون درج کلید API در کد، فقط از env یا فایل .env

## نصب روی Windows

### گام 1: نصب Python

از سایت python.org نسخه 3.11 یا بالاتر را نصب کنید و گزینه Add Python to PATH را تیک بزنید.

### گام 2: ساخت Virtual Environment

در PowerShell در پوشه پروژه اجرا کنید:

    cd voice_to_text
    python -m venv venv
    .\venv\Scripts\activate

### گام 3: نصب پکیج ها

    pip install --upgrade pip
    pip install -r requirements.txt

اگر فقط حالت Local را می خواهید، می توانید خطوط openai و google-cloud-speech را از requirements.txt حذف کنید.

## دانلود یکباره مدل - مهمترین گام برای دقت و سرعت

قبل از اجرای برنامه، مدل Whisper را یک بار دانلود کنید تا همیشه به صورت آفلاین در دسترس باشد:

    python download_model.py medium

- مدل medium برای فارسی دقیق تر است و از small بسیار بهتر عمل می کند.
- اگر GPU قوی دارید می توانید large-v3 را امتحان کنید که بهترین دقت را دارد ولی سنگین است.
- اگر سیستم خیلی ضعیفی دارید، small کمترین گزینه قابل قبول برای فارسی است.
- مدل در پوشه voice_to_text/models/faster-whisper-medium/ ذخیره می شود و همیشه باقی می ماند.

پس از این مرحله، برنامه بدون نیاز به اینترنت اجرا می شود.

## اجرای برنامه

    python main.py

اگر همه چیز درست باشد:

1. پنجره با تم تاریک باز می شود.
2. نوار سطح صدا با صحبت کردن شما حرکت می کند.
3. با Ctrl+Shift+Space یا دکمه شروع ضبط، ضبط را شروع کنید.
4. با دکمه توقف، ضبط تمام شده و متن تبدیل می شود.

## تنظیمات فایل .env

فایل .env.example را به .env کپی و مقادیر را تنظیم کنید:

    copy .env.example .env

نمونه محتوا:

    WHISPER_MODEL=medium
    WHISPER_DEVICE=auto
    WHISPER_COMPUTE_TYPE=auto
    WHISPER_LANGUAGE=fa
    DEFAULT_PROVIDER=local
    LOG_LEVEL=INFO

## انتخاب مدل Whisper - تفاوت سرعت و دقت

| مدل        | حجم تقریبی | سرعت روی CPU  | دقت                | مناسب برای            |
|------------|------------|---------------|--------------------|-----------------------|
| tiny       | 39 MB      | بسیار سریع    | ضعیف               | فقط تست               |
| base       | 74 MB      | سریع          | متوسط رو به پایین  | انگلیسی ساده          |
| small      | 244 MB     | متوسط         | قابل قبول          | حداقل برای فارسی      |
| medium     | 769 MB     | کند           | خوب                | پیشنهاد برای فارسی    |
| large-v3   | 1.5 GB     | خیلی کند      | بهترین             | GPU و دقت حداکثری     |

نکته مهم: مدل Whisper روی فارسی به طور کلی از انگلیسی ضعیف تر عمل می کند.
هرچه مدل بزرگتر باشد، تعداد اشتباهات فارسی به شدت کم می شود.
برای استفاده روزمره، حداقل مدل medium را توصیه می کنیم.

## استفاده از GPU - کارت گرافیک NVIDIA با CUDA

اگر کارت گرافیک NVIDIA با پشتیبانی CUDA دارید، دقت و سرعت به شدت بهبود می یابد.

### گام 1: نصب PyTorch با CUDA

    pip install torch --index-url https://download.pytorch.org/whl/cu121

### گام 2: تنظیم فایل .env

    WHISPER_DEVICE=cuda
    WHISPER_COMPUTE_TYPE=float16

### گام 3: دانلود مدل بزرگتر

    python download_model.py large-v3

و در فایل .env:

    WHISPER_MODEL=large-v3

با این تنظیمات، دقت فارسی به طور چشمگیری بالا می رود و سرعت هم عالی است.

## Provider های اختیاری - API

پیش فرض حالت local است و هیچ اینترنتی لازم نیست.
برای استفاده از API های ابری:

### OpenAI Whisper API

در فایل .env:

    OPENAI_API_KEY=sk-your-key-here
    OPENAI_WHISPER_MODEL=whisper-1
    DEFAULT_PROVIDER=openai

### Google Cloud Speech-to-Text

در فایل .env:

    GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
    DEFAULT_PROVIDER=google

سپس در برنامه از کمبوباکس Provider، حالت موردنظر را انتخاب کنید.

## کلیدهای میانبر

| میانبر              | عملکرد            |
|---------------------|-------------------|
| Ctrl+Shift+Space    | شروع یا توقف ضبط  |
| Ctrl+S              | ذخیره در فایل TXT |
| Ctrl+L              | پاک کردن متن      |
| Ctrl+C در Editor    | کپی انتخاب شده    |

## ساخت فایل اجرایی EXE با PyInstaller

    pip install pyinstaller
    python build_exe.py

خروجی در پوشه dist/VoiceToText/ قرار می گیرد.
برای اجرا روی سیستم دیگر، کل پوشه را کپی کنید. پوشه models را هم در کنار فایل اجرایی قرار دهید تا آفلاین کار کند.

## عیب یابی

| مشکل                       | راه حل                                                              |
|----------------------------|---------------------------------------------------------------------|
| میکروفون پیدا نمی شود      | در Windows > Settings > Privacy > Microphone دسترسی را فعال کنید   |
| نوار سطح صدا حرکت نمی کند  | میکروفون دیگری را از کمبوباکس انتخاب کنید یا میکروفون پیش فرض را چک کنید |
| خیلی کند است               | مدل کوچکتر مثل small یا base یا compute_type=int8 انتخاب کنید      |
| دقت فارسی پایین است        | مدل medium یا large-v3 را دانلود و انتخاب کنید                      |
| GPU استفاده نمی شود        | درایور NVIDIA به همراه CUDA نصب کنید و PyTorch با cu121 نصب کنید   |
| خطای دانلود مدل            | یک بار python download_model.py medium را با اینترنت اجرا کنید     |
| متن فارسی خراب می شود      | فونت های Vazirmatn یا Segoe UI را نصب کنید                          |

## ساختار پروژه

    voice_to_text/
    ├── models/                       مدل های دانلودشده Whisper
    ├── app/
    │   ├── audio/                    ضبط و دستگاه ها
    │   ├── config/                   تنظیمات و فایل .env
    │   ├── providers/                Local / OpenAI / Google
    │   ├── speech/                   Interface مشترک
    │   ├── ui/                       پنجره، استایل، سطح صدا
    │   └── utils/                    Logging و متن فارسی
    ├── main.py
    ├── download_model.py
    ├── build_exe.py
    ├── requirements.txt
    ├── .env.example
    └── README.md

## لایسنس

MIT