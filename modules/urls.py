from django.urls import re_path
from rest_framework_simplejwt import views 
from modules import views

urlpatterns = [
    re_path('modules/?$', views.ModulesView.as_view(), name='get-modules'),
    re_path('modules/<module_code>/?$', views.ModuleView.as_view(), name='get-module'),
    re_path('modules/<module_code>/users/?$', views.ModuleUsersView.as_view(), name='get-module-users'),
    re_path('modules/update/<academic_year>/?$', views.ModuleUpdateView.as_view(), name='update-modules'),
    re_path('modules/update/manual/<academic_year>/?$', views.ModuleManualUpdateView.as_view(), name='update-modules'),
]
