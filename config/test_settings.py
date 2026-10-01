"""Настройки для pytest (см. pytest.ini): те же, что config/settings.py, плюс ключ.

Ключ случайный на каждый запуск — в коде нет ни одного реального или «дефолтного» секрета.
"""
import os
import secrets

os.environ.setdefault("SECRET_KEY", "test-" + secrets.token_urlsafe(32))

from config.settings import *  # noqa: E402,F401,F403

# Быстрый хешер только для тестов: create_user в каждом тесте не тратит ~0,3 с на PBKDF2.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
