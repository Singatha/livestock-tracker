from urllib.parse import urlparse

from django.conf import settings
from django.core.checks import Tags, Warning, register


@register(Tags.security, deploy=True)
def check_production_security(app_configs, **kwargs):
    warnings = []
    cache_backend = settings.CACHES["default"]["BACKEND"]
    if cache_backend.endswith("LocMemCache"):
        warnings.append(
            Warning(
                "Production throttling requires a cache shared by every API worker.",
                hint="Set DJANGO_CACHE_URL to a dedicated Redis database.",
                id="flockwise.W001",
            )
        )

    if settings.SECURE_SSL_REDIRECT:
        frontend_url = urlparse(settings.FRONTEND_BASE_URL)
        if frontend_url.scheme != "https":
            warnings.append(
                Warning(
                    "FRONTEND_BASE_URL must use HTTPS when SSL redirects are enabled.",
                    hint="Set FRONTEND_BASE_URL to the public HTTPS application origin.",
                    id="flockwise.W002",
                )
            )

    if settings.REST_FRAMEWORK.get("NUM_PROXIES", 0) < 1:
        warnings.append(
            Warning(
                "The production reverse-proxy count is not configured.",
                hint="Set DJANGO_NUM_PROXIES to the exact number of trusted proxies.",
                id="flockwise.W003",
            )
        )
    return warnings
