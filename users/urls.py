from django.urls import re_path
from rest_framework_simplejwt import views as jwt_views
from . import views

urlpatterns = [
    re_path('register/?$', views.RegisterView.as_view(), name='register'),
    re_path('otp/verify/?$', views.OtpVerifyView.as_view(), name='otp_verify'),
    re_path('otp/send/?$', views.OtpSendView.as_view(), name='otp_send'),
    re_path('login/?$', views.LoginView.as_view(), name='login'),
    re_path('logout/?$', jwt_views.TokenBlacklistView.as_view(), name='logout'),
    re_path('token/refresh/?$', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    re_path('token/verify/?$', jwt_views.TokenVerifyView.as_view(), name='token_verify'),
    re_path('user/modules/?$', views.StudentModulesView.as_view(), name='student_modules'),
    re_path('user/?$', views.StudentSelfView.as_view(), name='student_self'),
    re_path('user/picture/?$', views.ProfilePictureView.as_view(), name='profile_picture'),
    re_path(r'user/(?P<id>\d+)/?$', views.StudentDetailView.as_view(), name='student_detail'),
    re_path('user/modules/enroll/?$', views.StudentEnrollView.as_view(), name='enroll_module'),
    re_path(r'user/modules/status/(?P<module_code>\w+)/?$', views.ModuleStatusView.as_view(), name='update_module_status'),
    re_path('user/connections/?$', views.UserConnectionView.as_view(), name='user_connections'),
]