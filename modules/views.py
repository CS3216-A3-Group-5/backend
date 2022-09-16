from django.shortcuts import render
from rest_framework import viewsets

from .serializers import ModuleSerializer
from .models import Module

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Module.objects.all().order_by('module_code')
    serializer_class = ModuleSerializer
    
