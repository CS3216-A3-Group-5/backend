from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('otp/verify/', views.OtpVerifyView.as_view(), name='otp_verify'),
    path('otp/send/', views.OtpSendView.as_view(), name='otp_send'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', jwt_views.TokenBlacklistView.as_view(), name='logout'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', jwt_views.TokenVerifyView.as_view(), name='token_verify'),
]