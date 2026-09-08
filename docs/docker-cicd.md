# Docker و CI/CD پروژه مدیریت هزینه

## Dockerfile عادی و چندمرحله‌ای

در Dockerfile تک‌مرحله‌ای، ابزار نصب dependencyها و فایل‌های موقت build داخل همان
image اجرای برنامه باقی می‌مانند. این روش ساده است، اما معمولاً image نهایی را
بزرگ‌تر می‌کند.

در Dockerfile چندمرحله‌ای، build و runtime از هم جدا می‌شوند. فقط خروجی لازم از
مرحله build وارد image نهایی می‌شود؛ بنابراین image اجرایی ساده‌تر و کم‌حجم‌تر است.

| روش | مزیت | محدودیت |
| --- | --- | --- |
| تک‌مرحله‌ای | نوشتن و درک اولیه آسان‌تر | image بزرگ‌تر و ابزارهای اضافی در runtime |
| چندمرحله‌ای | image نهایی تمیزتر و امن‌تر | دارای بیش از یک stage در Dockerfile |

Dockerfile این پروژه فقط دو مرحله دارد:

- `builder`: نصب dependencyهای production با uv و `uv.lock`
- `runtime`: اجرای FastAPI با virtual environment آماده و کاربر غیر root

فایل‌های تست، مستندات، GitHub Actions و محیط محلی نیز با `.dockerignore` وارد build
context نمی‌شوند.

ساخت image به‌صورت محلی:

```bash
docker build --target runtime --tag expense-manager:local .
```

## CI

فایل CI در `.github/workflows/ci.yml` قرار دارد و هنگام Pull Request به `main` یا
اجرای دستی فعال می‌شود.

CI یک job دارد و اقدامات زیر را انجام می‌دهد:

1. اجرای PostgreSQL و Redis آزمایشی
2. نصب Python 3.13 و dependencyها با uv
3. بررسی lockfile، format و lint با Ruff
4. اجرای migration و بررسی هماهنگی مدل‌ها با Alembic
5. اجرای تست‌ها با pytest
6. ساخت Docker image
7. بررسی کاربر غیر root و import شدن برنامه داخل image

CI هیچ imageای را منتشر نمی‌کند و فقط معتبر بودن تغییرات را بررسی می‌کند.

## CD

فایل CD در `.github/workflows/cd.yml` قرار دارد و بعد از push به `main` اجرا می‌شود.

CD اقدامات زیر را انجام می‌دهد:

1. ورود به GitHub Container Registry با `GITHUB_TOKEN`
2. ساخت stage نهایی Dockerfile
3. انتشار image در GHCR با دو tag

```text
ghcr.io/triplem8360/expense-manager:latest
ghcr.io/triplem8360/expense-manager:sha-<commit-sha>
```

این مرحله Continuous Delivery تا رجیستری است. برای استقرار روی یک سرور واقعی باید
اطلاعات مقصد و secretهای همان محیط مشخص شوند؛ به همین دلیل deployment سرور در این
تمرین اضافه نشده است.

## تنظیمات GitHub

- در branch protection برنچ `main`، check مربوط به
  `Test and build application` را اجباری کنید.
- دسترسی GitHub Actions برای نوشتن package را بررسی کنید.
- بعد از اولین انتشار، visibility مربوط به package را در بخش Packages تنظیم کنید.
- secretهای برنامه را داخل Dockerfile یا workflow قرار ندهید؛ آن‌ها باید هنگام
  اجرای container فراهم شوند.

## منابع

- [Docker: Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Docker build best practices](https://docs.docker.com/build/building/best-practices/)
- [GitHub Actions: Building and testing Python](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [GitHub Actions: Publishing Docker images](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images)

