"""
Django settings for clairvoyance project.

Generated by 'django-admin startproject' using Django 2.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
try:
    from key import SECRET_KEY, LDAP_PASSWORD, LDAP_CERT_PATH # Imports sec. key
except ImportError:
    SECRET_KEY = "0"

import environ

env = environ.Env()
environ.Env.read_env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['gfr2.petnet.rh.dk', 'gfr2', '172.16.186.190', '193.3.238.103', '172.16.78.176', '127.0.0.1', 'localhost', 'kylle', 'gfr', 'gfr.petnet.rh.dk', 'kylle.petnet.rh.dk']

AUTH_USER_MODEL = 'main_page.User'
AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'main_page.backends.SimpleBackend'
]

AUTH_LDAP_SERVER_URI = 'ldap://regionh.top.local'
AUTH_LDAP_START_TLS  = True                  # Ensures Encryption

# AUTH LOGINENV_VAR_SEARCH_CACHE_PATH

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django_auth_ldap": {"level": "DEBUG", "handlers": ["console"]}},
}


LOGIN_URL = '/'

# Application definition

INSTALLED_APPS = [
    'main_page',
    'bootstrap4',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clairvoyance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'clairvoyance.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

GFR_DATABASE_NAME = env("GFR_DATABASE_NAME")
GFR_DATABASE_USER = env("GFR_DATABASE_USER")
GFR_DATABASE_PW   = env("GFR_DATABASE_PW")
GFR_DATABASE_HOST = env("GFR_DATABASE_HOST")

DATABASES = {
    'default': {
      #'ENGINE': 'django.db.backends.sqlite3',
      #'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
      #'CONN_MAX_AGE': 1,
      'ENGINE'    : 'django.db.backends.mysql',
      'NAME'      : GFR_DATABASE_NAME,
      'USER'      : GFR_DATABASE_USER,
      'PASSWORD'  : GFR_DATABASE_PW,
      'HOST'      : GFR_DATABASE_HOST,
      'PORT'      : '3306'
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'CET'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "main_page/static/")

GFR_LOGGER_PATH = env("GFR_LOG_PATH")
RIS_THREAD_LOG_PATH = env("RIS_THREAD_LOG_PATH")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false' : {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true' : {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        },
        'GFRFormatter': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '{server_time} {funcName} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter' : 'django.server'
        },
        'GFRHandler': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': GFR_LOGGER_PATH,
            'formatter': 'GFRFormatter',
            'when': 'D',
            'backupCount': 0, # Keeps all backups
        },
        'RisThreadHandler': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': RIS_THREAD_LOG_PATH,
            'formatter': 'GFRFormatter',
            'when': 'D',
            'backupCount': 0, # Keeps all backups
        }
    },
    'loggers' : {
        'GFRLogger' : {
            'handlers' : ['GFRHandler'],
            'level': 'INFO'
        },
        'RisThread' : {
            'handlers' : ['RisThreadHandler'],
            'level': 'INFO',
        },
    },
}
