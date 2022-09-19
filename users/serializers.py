from django.contrib.auth import authenticate
from rest_framework import exceptions
from rest_framework import serializers

from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'nus_email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['nus_email'], validated_data['password'])

        return user

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
    