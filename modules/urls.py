from django.urls import path
from rest_framework_simplejwt import views 
from modules import views

urlpatterns = [
    path('modules/', views.ModulesView.as_view(), name='get-modules'),
    path('modules/<module_code>/', views.ModuleView.as_view(), name='get-module'),
    path('modules/<module_code>/users/', views.ModuleUsersView.as_view(), name='get-module-users'),
    path('modules/update/<academic_year>/', views.ModuleUpdateView.as_view(), name='update-modules'),
    path('modules/update/manual/<academic_year>/', views.ModuleManualUpdateView.as_view(), name='update-modules'),
]
