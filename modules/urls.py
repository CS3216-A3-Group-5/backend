from django.urls import path
from rest_framework_simplejwt import views 
from modules import views

urlpatterns = [
    path('modules/', views.ModuleViewSet.as_view({'get': 'list'}), name='get-modules'),
    
]