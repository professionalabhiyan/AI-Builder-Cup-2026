from django.urls import path
from .views import (
    AuthLoginAPIView,
    TwoFASetupAPIView,
    TwoFAVerifyAPIView,
    UserManagementAPIView,
    health_check_view,
)

urlpatterns = [
    path('health/', health_check_view, name='api-health'),
    path('auth/login/', AuthLoginAPIView.as_view(), name='auth-login'),
    path('auth/2fa/setup/', TwoFASetupAPIView.as_view(), name='auth-2fa-setup'),
    path('auth/2fa/verify/', TwoFAVerifyAPIView.as_view(), name='auth-2fa-verify'),
    path('users/', UserManagementAPIView.as_view(), name='users-crud'),
]
