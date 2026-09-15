import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-development-only")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1,isaacbampoeaddo.com").split(",")]
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "hub"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware"]
ROOT_URLCONF = "config.urls"
TEMPLATES = []
WSGI_APPLICATION = "config.wsgi.application"
database_url = urlparse(os.environ.get("DATABASE_URL", "postgresql://oko:atteh@db:5432/oko_atteh"))
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "NAME": database_url.path.lstrip("/"), "USER": database_url.username, "PASSWORD": database_url.password, "HOST": database_url.hostname, "PORT": database_url.port or 5432}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/app/media"))
MEDIA_URL = "/media/"
USE_TZ = True
TIME_ZONE = "Africa/Accra"
