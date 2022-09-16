from unicodedata import name
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer

from rest_framework import serializers

from .models import User

class TokenObtainPairSerializer(JwtTokenObtainPairSerializer):
    default_error_messages = {
        'nus_email_unverified': _('NUS Email is not verified')
    }

    def validate(self, attrs):
        nus_email = attrs.get('nus_email')
        user = User.objects.filter(nus_email=nus_email).first()
        
        if user and not user.is_verified:
            raise exceptions.AuthenticationFailed(
                self.error_messages['nus_email_unverified'],
                'nus_email_unverified',
            )

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
    