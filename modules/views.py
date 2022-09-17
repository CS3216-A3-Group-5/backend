from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets

from .serializers import ModuleSerializer
from users.serializers import SimpleUserSerializer
from .models import Module
from users.models import User, Enrolment, Connections

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ModuleSerializer

    def get_queryset(self):
        queryset = Module.objects.all().order_by('module_code')
        search_query = self.request.query_params.get('q')
        if search_query is not None:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(module_code__icontains=search_query))
        return queryset


class ModuleUsersViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SimpleUserSerializer

    
    #requester = request.user

    def get_queryset(self):
        queryset = Enrolment.objects.all()
        module_code = self.kwargs['module_code']
        queryset = queryset.filter(module__iexact=module_code)
        return queryset

