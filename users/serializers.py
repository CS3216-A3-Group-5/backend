from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from modules.serializers import ModuleSerializer

from .models import Connection, Connection_Status, Enrolment, User, User_Status

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'nus_email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['nus_email'], validated_data['password'])

        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'nus_email', 'telegram_id', 'phone_number', 'year', 'major', 'bio']

class SimpleUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    year = serializers.IntegerField()
    major = serializers.CharField()
    user_status = serializers.SerializerMethodField()  # based on module
    connection_status = serializers.SerializerMethodField()  #based on module and user token

    def get_user_status(self, obj):
        module_code = self.context.get('module_code')
        enrolment = Enrolment.objects.get(user=obj, module__module_code__iexact=module_code)
        return User_Status[enrolment.status].value
        
    def get_connection_status(self, obj):
        # get Connections table filtered by requester or accepter being user making api request
        # for each user, check if in this filtered table
        # if in table, return connection status
        # else no connection
        user = self.context.get('user')
        module_code = self.context.get('module_code')

        queryset = Connection.objects.filter(Q(requester=user, accepter=obj) | Q(requester=obj, accepter=user))
        if queryset.exists():
            record = queryset.first()
            return Connection_Status[record.status].value
        else:
            return 0

class ConnectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    module = ModuleSerializer()
    other_user = serializers.SerializerMethodField()

    def get_other_user(self, obj):
        user = self.context.get('user')
        if obj.requester == user:
            other_user = obj.accepter
        else:
            other_user = obj.requester
        return SimpleUserSerializer(other_user, context={'user': user, 'module_code': obj.module.module_code}).data