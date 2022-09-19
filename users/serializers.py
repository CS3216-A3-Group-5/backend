from enum import Enum
from unicodedata import name
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.fields import CurrentUserDefault
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer

from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer

from .models import Connections, User, Enrolment


class TokenObtainPairSerializer(JwtTokenObtainPairSerializer):
    def validate(self, attrs):
        nus_email = attrs.get('nus_email')
        password = attrs.get('password')
        try:
            request = self.context["request"]
        except KeyError:
            pass
        
        user = authenticate(request, nus_email=nus_email, password=password)

        if not user:
            return {
                'error_code': 1,
                'error_message': 'Email and/or password is incorrect.'
            }

        return super().validate(attrs)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'nus_email', 'telegram_id', 'phone_number', 'year', 'major', 'bio']

class SimpleUserSerializer(serializers.Serializer):
    id = serializers.IntegerField(source = 'user.id')
    username = serializers.CharField(max_length=50, source='user.username')
    first_name = serializers.CharField(max_length=50, source='user.first_name')
    last_name = serializers.CharField(max_length=50, source='user.last_name')
    year = serializers.IntegerField(source='user.year')
    major = serializers.CharField(max_length=20, source='user.major')
    bio = serializers.CharField(source='user.bio')
    user_status = serializers.SerializerMethodField()  # based on module
    connection_status = serializers.SerializerMethodField()  #based on module and user token

    def get_user_status(self, obj):
        if obj.status == 'LF':
            return 1
        elif obj.status == 'WH':
            return 2
        else:
            return 0
        
    def get_connection_status(self, obj):
        # get Connections table filtered by requester or accepter being user making api request
        # for each user, check if in this filtered table
        # if in table, return connection status
        # else no connection
        user = None
        user = self.context.get('user')
        module_code = self.context.get('module_code')

        queryset = Connections.objects.filter(Q(requester=user) | Q(accepter=user), module__module_code__iexact=module_code)

        record = queryset.get(Q(requester__exact=obj.user) | Q(accepter__exact=obj.user))
        if record.status == 'AC':
            return 2
        elif record.status == 'PD':
            return 1
        else:
            return 0

        
