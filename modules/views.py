from enum import Enum
from urllib import request
from django.db.models import Q
from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .serializers import ModuleSerializer
from users.serializers import SimpleUserSerializer
from .models import Module
from users.models import User, Enrolment, Connections

from modules import serializers

class ModuleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ModuleSerializer
    
    def get_queryset(self):
        queryset = Module.objects.all().order_by('module_code')
        search_query = self.request.query_params.get('q')
        paginator = PageNumberPagination()
        if search_query is not None:
            queryset = queryset.filter(Q(title__icontains=search_query) | Q(module_code__icontains=search_query)).order_by('module_code', 'title')
        queryset = paginator.paginate_queryset(queryset, self.request)
        return queryset


class User_Status(Enum):
    NL = 0
    LF = 1
    WH = 2
class Connection_Status(Enum):
    RJ = 0
    PD = 1
    AC = 2

class ModuleUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, module_code):
        name = request.query_params.get('name')
        user_status = request.query_params.get('user_status')
        connection_status = request.query_params.get('connection_status')
        paginator = PageNumberPagination()
        enrolments = Enrolment.objects.all().filter(Q(module__module_code__iexact=module_code), ~Q(user__exact=request.user)).order_by('user')

        if name is not None:
            enrolments = enrolments.filter(Q(user__first_name__icontains=name) | Q(user__last_name__icontains=name))
        if user_status is not None:
            status = User_Status(int(user_status)).name
            enrolments = enrolments.filter(status__iexact=status)

        
        if connection_status is not None:
            # all connections where request.user is involved in, for target module_code, and target connection_status
            connections = Connections.objects.filter(Q(requester=request.user) | Q(accepter=request.user), module__module_code__iexact=module_code)
            status = Connection_Status(int(connection_status)).name
            connections = connections.filter(status__iexact=status)
            users = connections.values_list('requester', flat=True).union(connections.values_list('accepter', flat=True))
            enrolments = enrolments.filter(user__in=users)

        queryset = paginator.paginate_queryset(enrolments, request)
        serializer = SimpleUserSerializer(queryset, many=True, context={'user': request.user, 'module_code': module_code})
        return Response(serializer.data)

