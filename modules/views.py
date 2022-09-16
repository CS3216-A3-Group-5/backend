from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets

from .serializers import ModuleSerializer
from .models import Module

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ModuleSerializer

    def get_queryset(self):
        queryset = Module.objects.all().order_by('module_code')
        search_query = self.request.query_params.get('q')
        if search_query is not None:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(module_code__icontains=search_query))
        return queryset
