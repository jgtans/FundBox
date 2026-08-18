"""
URL configuration for fundbox project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from collects.views import CollectViewSet, PaymentViewSet

router = DefaultRouter()
router.register("collects", CollectViewSet, basename="collects")
router.register("payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path("admin/", admin.site.urls),
    # JWT + регистрация через Djoser (K5)
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    # API
    path("api/", include(router.urls)),
    # Документация Swagger (K8)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
