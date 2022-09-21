from enum import Enum
from multiprocessing import context
from urllib import request
from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

import requests

from .serializers import ModuleSerializer
from users.serializers import SimpleUserSerializer
from .models import Module
from users.models import Connection_Status, User, Enrolment, Connection, User_Status

from modules import serializers

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ModuleSerializer

    def get_serializer_context(self):
        context = super(ModuleViewSet, self).get_serializer_context()
        context.update({'user': self.request.user})
        return context
    
    def get_queryset(self):
        queryset = Module.objects.all().order_by('module_code')
        search_query = self.request.query_params.get('q')
        paginator = PageNumberPagination()
        if search_query is not None:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(module_code__icontains=search_query)).order_by('module_code', 'title')
        queryset = paginator.paginate_queryset(queryset, self.request)
        return queryset



class ModuleUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, module_code):
        name_filter = request.query_params.get('name')
        user_status_filter = request.query_params.get('user_status')
        connection_status_filter = request.query_params.get('connection_status')
        paginator = PageNumberPagination()
        enrolments = Enrolment.objects.all().filter(Q(module__module_code__iexact=module_code), ~Q(user__exact=request.user)).order_by('user')

        if name_filter is not None:
            enrolments = enrolments.filter(Q(user__first_name__icontains=name_filter) | Q(user__last_name__icontains=name_filter))
        if user_status_filter is not None:
            status = User_Status(int(user_status_filter)).name
            enrolments = enrolments.filter(status__iexact=status)
        # Don't include enrolments of users not looking for matches.
        enrolments = enrolments.exclude(status__iexact='NL')

        
        if connection_status_filter is not None:
            # all connections where request.user is involved in, for target module_code, and target connection_status
            connections = Connection.objects.filter(Q(requester=request.user) | Q(accepter=request.user), module__module_code__iexact=module_code)
            status = Connection_Status(int(connection_status_filter)).name
            connections = connections.filter(status__iexact=status)
            users = connections.values_list('requester', flat=True).union(connections.values_list('accepter', flat=True))
            enrolments = enrolments.filter(user__in=users)

        users = User.objects.filter(id__in=enrolments.values_list('user', flat=True).distinct()).order_by('id')

        # all users who are in the module, with filters
        queryset = paginator.paginate_queryset(users, request)
        serializer = SimpleUserSerializer(queryset, many=True, context={'user': request.user, 'module_code': module_code})
        return Response(serializer.data)

class ModuleUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, academic_year):
        url = 'https://www.api.nusmods.com/v2/' + academic_year + '/moduleList.json'
        r = requests.get(url)
        data = r.json()

        for module in data:
            new_module_code = module["moduleCode"]
            new_title = module["title"]
            new_module, created = Module.objects.get_or_create(title=new_title, module_code=new_module_code)
            new_module.save()
        return Response(data)

class ModuleManualUpdateView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, academic_year):
        user = request.user
        data = request.data

        try:
            obj = data
            for m in data:
                module_code = m["module_code"]
                title = m["title"]
                new_module, created = Module.objects.get_or_create(title=new_title, module_code=new_module_code)
                new_module.save()
            return Response(Module.objects.all())
        except:
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)

class ModuleView(APIView):

    def get(self, request, module_code):
        user = request.user
        try:
            module = Module.objects.get(module_code__iexact=module_code)
            serializer = ModuleSerializer(module, context={'user': user})
            return Response(serializer.data)
        except:
            return Response("Module not found.", status=status.HTTP_404_NOT_FOUND)