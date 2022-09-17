from django.urls import path
from rest_framework_simplejwt import views 
from modules import views

urlpatterns = [
    path('modules/', views.ModuleViewSet.as_view({'get': 'list'}), name='get-modules'),
    path('modules/<module_code>/users', views.ModuleUsersViewSet.as_view({'get': 'list'}), name='get-module-users')
]
