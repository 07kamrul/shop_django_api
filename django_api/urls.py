from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("", RedirectView.as_view(url="/swagger/index.html", permanent=False)),
    path("api/", include("shop.urls")),
    # API Documentation
    path("swagger/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/index.html", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("swagger/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
