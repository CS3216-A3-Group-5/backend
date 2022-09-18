from unicodedata import name
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework.fields import CurrentUserDefault
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer

from rest_framework import serializers

from .models import Connections, User, Enrolment


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
    name = serializers.CharField(max_length=50, source='user.username')
    user_status = serializers.SerializerMethodField() #serializers.IntegerField() # based on module
    connection_status = serializers.SerializerMethodField() #serializers.IntegerField() #based on module and user token
    #connection_status = serializers.PrimaryKeyRelatedField(queryset = )
    #print(CurrentUserDefault())

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
        user = self.context.get("user")
        
        if not user.id:
            return 0

        queryset = Connections.objects.filter(Q(requester=user) | Q(accepter=user))
        try:
            record = queryset.get(Q(requester__exact=obj.user) | Q(accepter__exact=obj))
            if record.status == 'AC':
                return 2
            elif record.status == 'PD':
                return 1
            else:
                return 0

        except:
            return 20

        return 0
    
class UserSerializer(serializers.ModelSerializer):
    #enrolment = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    class Meta:
        model = User
        fields = ('username, nus_email', 'enrolment')

class EnrolmentSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')
    class Meta:
        model = Enrolment
        fields = ('user', 'module', 'status')
        depth = 1