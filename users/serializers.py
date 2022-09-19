from django.contrib.auth import authenticate
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer

from .models import User

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

class SimpleUserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, source='user.name')
    user_status = serializers.SerializerMethodField() #serializers.IntegerField() # based on module
    connection_status = serializers.SerializerMethodField() #serializers.IntegerField() #based on module and user token

    def user_status(self, obj):
        if obj.status == 'LF':
            return 1
        elif obj.status == 'WH':
            return 2
        else:
            return 0
        
    def connection_status(self, obj):
        # get Connections table filtered by sender or receiver being user making api request
        # for each user, check if in this filtered table
        # if in table, return connection status
        # else no connection
        return 0
    