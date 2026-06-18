from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'presentacion.sqlite3',
    }
}
DEBUG = True
ALLOWED_HOSTS = ['*']
