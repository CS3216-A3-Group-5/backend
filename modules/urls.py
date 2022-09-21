from django.urls import re_path
from rest_framework_simplejwt import views 
from modules import views

urlpatterns = [
    re_path(r'modules/?$', views.ModulesView.as_view(), name='get-modules'),
    re_path(r'modules/(?P<module_code>\w+)/?$', views.ModuleView.as_view(), name='get-module'),
    re_path(r'modules/(?P<module_code>\w+)/users/?$', views.ModuleUsersView.as_view(), name='get-module-users'),
    re_path(r'modules/update/(?P<academic_year>[\w-]+)/?$', views.ModuleUpdateView.as_view(), name='update-modules'),
    re_path(r'modules/update/manual/(?P<academic_year>[\w-]+)/?$', views.ModuleManualUpdateView.as_view(), name='update-modules'),
]
