from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import healthcheck

urlpatterns = [
    path("healthz/", healthcheck, name="healthcheck"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/audit/", include("apps.audit.urls")),
    path("api/v1/attachments/", include("apps.attachments.urls")),
    path("api/v1/farms/", include("apps.farms.urls")),
    path("api/v1/animals/", include("apps.animals.urls")),
    path("api/v1/health/", include("apps.health.urls")),
    path("api/v1/husbandry/", include("apps.husbandry.urls")),
    path("api/v1/reproduction/", include("apps.reproduction.urls")),
    path("api/v1/growth/", include("apps.growth.urls")),
    path("api/v1/medicine/", include("apps.medicine.urls")),
    path("api/v1/imports/", include("apps.imports.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/nutrition/", include("apps.nutrition.urls")),
    path("api/v1/reports/", include("apps.reports.urls")),
    path("api/v1/dashboard/", include("apps.dashboard.urls")),
]
