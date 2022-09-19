from django.urls import path
from rest_framework_simplejwt import views as jwt_views
from . import views

urlpatterns = [
    path('token/', views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', jwt_views.TokenVerifyView.as_view(), name='token_verify'),
    path('users/modules/', views.StudentModulesView.as_view(), name='student_modules'),
    path('users/', views.StudentSelfView.as_view(), name='student_self'),
    path('users/<id>/', views.StudentDetailView.as_view(), name='student_detail'),
]