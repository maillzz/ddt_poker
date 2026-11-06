"""Статика под gunicorn/Docker отдаётся WhiteNoise: без неё страницы в Docker — без стилей."""
from django.conf import settings


def test_whitenoise_serves_static_outside_debug():
    assert "whitenoise.middleware.WhiteNoiseMiddleware" in settings.MIDDLEWARE
    backend = settings.STORAGES["staticfiles"]["BACKEND"]
    assert backend.startswith("whitenoise"), backend
