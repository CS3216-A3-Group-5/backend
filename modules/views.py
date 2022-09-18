from urllib import request
from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import ModuleSerializer
from users.serializers import SimpleUserSerializer, EnrolmentSerializer, UserSerializer
from .models import Module
from users.models import User, Enrolment, Connections

from modules import serializers

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ModuleSerializer

    def get_queryset(self):
        queryset = Module.objects.all().order_by('module_code')
        search_query = self.request.query_params.get('q')
        if search_query is not None:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(module_code__icontains=search_query))
        return queryset


class ModuleUsersViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SimpleUserSerializer()
    permission_classes = [permissions.IsAuthenticated]


    def get_queryset(self):
        print(self.request.user)
        queryset = Enrolment.objects.all()
        module_code = self.kwargs['module_code']
        queryset = queryset.filter(module__module_code__iexact=module_code)
        return queryset

class ModuleUsersView(APIView):
    #permission_classes = [permissions.IsAuthenticated]
    def get(self, request, module_code, format=None):
        enrolments = Enrolment.objects.all().filter(module__module_code__iexact=module_code)
        serializer = SimpleUserSerializer(enrolments, many=True, context={'user': request.user})
        return Response(serializer.data)

