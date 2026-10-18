wfrom pathlib import Path
import os
import dj_database_url


# =========================================================
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-dev-only-change-this"
)

DEBUG = os.environ.get(
    "DEBUG",
    "True"
).lower() == "true"


# =========================================================
# ALLOWED HOSTS
# =========================================================

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "ALLOWED_HOSTS",
        "127.0.0.1,localhost"
    ).split(",")
    if host.strip()
]


# =========================================================
# CSRF TRUSTED ORIGINS
# =========================================================

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        ""
    ).split(",")
    if origin.strip()
]


# =========================================================
# PRODUCTION SECURITY SETTINGS
# =========================================================

# Render (and most hosts) terminate HTTPS at their proxy and forward the
# request to Django as plain HTTP. Without this header Django never sees
# the request as secure, so SECURE_SSL_REDIRECT=True causes an endless
# redirect loop.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = os.environ.get(
    "SECURE_SSL_REDIRECT",
    "False"
).lower() == "true"


SESSION_COOKIE_SECURE = os.environ.get(
    "SESSION_COOKIE_SECURE",
    "False"
).lower() == "true"


CSRF_COOKIE_SECURE = os.environ.get(
    "CSRF_COOKIE_SECURE",
    "False"
).lower() == "true"


SECURE_HSTS_SECONDS = int(
    os.environ.get(
        "SECURE_HSTS_SECONDS",
        "0"
    )
)


SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS",
    "False"
).lower() == "true"


SECURE_HSTS_PRELOAD = os.environ.get(
    "SECURE_HSTS_PRELOAD",
    "False"
).lower() == "true"


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'accounts',
    'users',
    'inventory',
    'sales',
    'purchase',
    'reports',
    'expenses',
    'credit',
    'proforma',
    'orders',
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =========================================================
# URL CONFIGURATION
# =========================================================

ROOT_URLCONF = 'config.urls'


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "orders.context_processors.active_order_count",
                "orders.context_processors.shop_config",
                "users.context_processors.unread_message_count",
            ],
        },
    },
]


# =========================================================
# WSGI
# =========================================================

WSGI_APPLICATION = 'config.wsgi.application'


# =========================================================
# DATABASE
# =========================================================

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator'
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator'
    },
]


# =========================================================
# INTERNATIONALIZATION
# =========================================================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Kigali'

USE_I18N = True

USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
# Uploaded files (product photos, payment proofs). On Render the normal
# disk is wiped on every deploy, so attach a Render Disk and set the
# MEDIA_ROOT environment variable to its mount path (e.g. /var/data/media).
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", BASE_DIR / 'media'))

STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]


# =========================================================
# STATIC FILE STORAGE
# =========================================================

STORAGES = {
    "default": {
        "BACKEND":
        "django.core.files.storage.FileSystemStorage",
    },

    "staticfiles": {
        "BACKEND":
        "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# =========================================================
# EMAIL
# =========================================================

MAILERS = {
    'default': {
        'BACKEND':
        'django.core.mail.backends.console.EmailBackend',
    },
}


# =========================================================
# LOGIN
# =========================================================

LOGIN_URL = "login"


# =========================================================
# SHOP (customer side) - static content, changed by editing here
# and pushing. Empty social URLs are simply not shown.
# =========================================================

SHOP = {
    "name": "GNT Partners",
    "company": "GNT Partners Ltd",
    "whatsapp": "250791816122",          # digits only, with country code
    "phone": "+250 791 816 122",
    "email": "gntpartners1@gmail.com",
    "address": "Kigali, Rwanda",
    "socials": {
        "facebook": "https://www.facebook.com/profile.php?id=100064463491249",
        "instagram": "https://www.instagram.com/gnt_partners?cplk=MW40YjVlZTNjcXRsOA==",
        "tiktok": "https://www.tiktok.com/@gnt.trust?is_from_webapp=1&sender_device=pc",
        "youtube": "https://youtube.com/@gntpartners?si=iB015KbGVcKs5sQH",
        "linkedin": "https://www.linkedin.com/company/gnt-trust/",
    },
    # Hero slider. "image" is a path under static/ (e.g. "shop/slides/1.jpg");
    # slides whose file does not exist yet are shown as colour slides.
    "slides": [
        {"title": "Quality products, Quality service",
         "text": "AMATARA, IBIKORESHO BYAMASHANYARAZI byose tubikugezaho",
         "image": "shop/slides/1.jpg"},
        {"title": "YOU ARE ALL WELCOME!",
         "text": " Get the best deal",
         "image": "shop/slides/2.jpg"},
        {"title": "MURAKAZA NEZA!",
         "text": "Tubahe ibikoresho byiza ",
         "image": "shop/slides/3.jpg"},
    ],
    # Optional background video (static/shop/background.mp4) and
    # still picture for phones (static/shop/background.jpg).
    "video": "shop/background.mp4",
    "video_poster": "shop/background.jpg",
    "default_message": "Hello, I would like to negotiate the price of this product.",
}
