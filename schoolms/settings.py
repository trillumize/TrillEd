import os
from pathlib import Path
from django.urls import reverse_lazy

# BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = 'django-insecure-=a$_3ggwxba($hfb^*nhk-8s5m=z41%_h*))wdz3_mg%$-_^00'
DEBUG = True
ALLOWED_HOSTS = ['*']


# settings.py
SHARED_APPS = (
    "django_tenants",   # required
    "schools",          # tenant model app
    "globals",          # global superadmins
    "django.contrib.contenttypes",
    "django.contrib.auth",       # must be here (for public schema)
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
)


TENANT_APPS = (
    "accounts",   # school users
    "academics",  # school-related models
)

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]



#INSTALLED_APPS = list(SHARED_APPS) + [a for a in TENANT_APPS if a not in SHARED_APPS]


# INSTALLED_APPS
#INSTALLED_APPS = list(SHARED_APPS) + list(TENANT_APPS) + ["rest_framework"]




SITE_ID = 1




# MIDDLEWARE
MIDDLEWARE = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "schools.middleware.TenantAdminMiddleware", 
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URLS and TEMPLATES
ROOT_URLCONF = "schoolms.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Add this
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "schoolms.wsgi.application"

# DATABASE (PostgreSQL + django-tenants)
DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": "schoolms",
        "USER": "postgres",
        "PASSWORD": "newpassword",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

# TENANT MODEL
TENANT_MODEL = "schools.Client"
TENANT_DOMAIN_MODEL = "schools.Domain"

# AUTH USER MODELS
# Public schema uses GlobalSuperAdmin
#AUTH_USER_MODEL = "globals.GlobalSuperAdmin"

# AUTH USER MODELS
#AUTH_USER_MODEL = "accounts.User"
# PUBLIC schema (superadmins)
AUTH_USER_MODEL = "globals.GlobalSuperAdmin"



# PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# INTERNATIONALIZATION
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# STATIC AND MEDIA
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR.parent / "media"

# LOGIN URLS
LOGIN_URL = reverse_lazy("academics:login")
LOGIN_REDIRECT_URL = reverse_lazy("academics:teacher_dashboard")

# EMAIL
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "school@example.com"
SCHOOL_NAME = "My High School"

# DEFAULT PK
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


AUTHENTICATION_BACKENDS = [
    'globals.backends.GlobalAdminAuthBackend',  # for public schema
    'accounts.backends.TenantAuthBackend',      # for tenant schemas
]