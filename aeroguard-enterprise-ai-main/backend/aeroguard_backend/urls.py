from django.contrib import admin
from django.urls import path, include
from core.views import portal_home_view, health_check_view, favicon_view

urlpatterns = [
    path('', portal_home_view, name='portal-home'),
    path('health/', health_check_view, name='health-check'),
    path('favicon.ico', favicon_view, name='favicon'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('core.urls')),
]
