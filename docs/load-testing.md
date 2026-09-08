# تست بار API با Locust

این پروژه از Locust برای شبیه‌سازی کاربران هم‌زمان و اندازه‌گیری رفتار API تحت بار
استفاده می‌کند. Locust داخل container مستقل اجرا می‌شود و به همین دلیل نیازی به نصب
آن در محیط Python پروژه نیست.

> تست بار را فقط روی محیطی اجرا کنید که برای آن مجوز دارید. اجرای این تست روی محیط
> production می‌تواند باعث افزایش مصرف CPU، connectionهای پایگاه داده و ایجاد
> کاربران آزمایشی شود.

## سناریوی تست

هر کاربر مجازی در ابتدای کار وارد سیستم می‌شود. اگر `LOAD_TEST_EMAIL` تنظیم نشده
باشد، ابتدا یک کاربر با email تصادفی ثبت می‌شود. سپس درخواست‌های زیر با وزن‌های
متفاوت اجرا می‌شوند:

- دریافت فهرست هزینه‌ها
- دریافت فهرست هزینه‌ها همراه با filter و sort
- دریافت جزئیات یک هزینه در صورت وجود داده
- دریافت وضعیت عمومی سرویس
- دریافت پیام فارسی endpoint چندزبانه

اگر `LOAD_TEST_EXPENSE_ID` تنظیم نشده باشد، Locust اولین شناسه موجود در فهرست
هزینه‌ها را انتخاب می‌کند. در پایگاه داده خالی، task جزئیات به خواندن فهرست تبدیل
می‌شود.

## تنظیمات

تنظیمات نمونه در `.env.docker.example` قرار دارند:

```dotenv
LOCUST_WEB_PORT=8089
LOCUST_TARGET_HOST=http://api:8000
LOAD_TEST_EMAIL=
LOAD_TEST_PASSWORD=LoadTestPassword123
LOAD_TEST_EXPENSE_ID=
LOAD_TEST_MAX_FAILURE_RATIO=0.01
LOAD_TEST_MAX_AVG_RESPONSE_MS=500
LOAD_TEST_MAX_P95_RESPONSE_MS=1000
```

برای اینکه زمان ثبت‌نام و password hashing وارد مرحله ramp-up نشود، می‌توانید یک
کاربر آزمایشی از قبل ایجاد کرده و email و password آن را در environment قرار دهید.

توکن‌های پروژه در cookieهای `Secure` ذخیره می‌شوند. ارتباط داخلی Compose از HTTP
استفاده می‌کند؛ بنابراین Locust پس از login مقدار access cookie را فقط در client
آزمایشی استخراج کرده و آن را به‌صورت صریح در هدر Cookie درخواست‌های محافظت‌شده
قرار می‌دهد. این رفتار تغییری در امنیت API واقعی ایجاد نمی‌کند.

## اجرا با رابط وب

```bash
docker compose --env-file .env.docker --profile loadtest up --build locust
```

سپس رابط Locust را در آدرس زیر باز کنید:

```text
http://localhost:8089
```

تعداد کاربران، نرخ ایجاد کاربران و مدت اجرا را متناسب با ظرفیت محیط انتخاب کنید.
برای شروع، 10 کاربر و spawn rate برابر 2 مقدار محافظه‌کارانه‌ای است.

## اجرای headless و تولید گزارش

ابتدا stack اصلی را اجرا کنید:

```bash
docker compose --env-file .env.docker up -d --build
```

سپس یک تست دو دقیقه‌ای اجرا کنید:

```bash
docker compose --env-file .env.docker --profile loadtest run --rm locust \
  --headless \
  --users 20 \
  --spawn-rate 2 \
  --run-time 2m \
  --html /reports/report.html \
  --csv /reports/results \
  --exit-code-on-error 1
```

گزارش HTML و فایل‌های CSV در `loadtest/reports` ایجاد می‌شوند و توسط Git نادیده
گرفته خواهند شد.

## توقف سرویس‌ها

```bash
docker compose --env-file .env.docker --profile loadtest down
```

برای جلوگیری از حذف داده PostgreSQL، در توقف معمولی از گزینه `--volumes` استفاده
نکنید.
