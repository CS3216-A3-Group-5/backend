from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Connection, Connection_Status, Enrolment, User, User_Status

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'nus_email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['nus_email'], validated_data['password'])

        return user

class SimpleUserSerializer(serializers.ModelSerializer):
    """Encapsulates a serializer that can serialize or deserialize a User with limited details."""
    user_status = serializers.SerializerMethodField()  # the user's enrolment status in a module
    connection_status = serializers.SerializerMethodField()  # the user's connection status with request.user

    class Meta:
        model = User
        fields = [
            'id', 
            'name', 
            'connection_status', 
            'user_status',
            'major',
            'year',
        ]

    def get_user_status(self, obj):
        module_code = self.context.get('module_code')
        enrolment = Enrolment.objects.get(user=obj, module__module_code__iexact=module_code)
        return User_Status[enrolment.status].value
        
    def get_connection_status(self, obj):
        user = self.context.get('user')

        if user is None:
            return 0

        return obj.get_connection_status_with(user)

class UserSerializer(SimpleUserSerializer):
    """Encapsulates a serializer that can serialize or deserialize a User without contact details."""

    class Meta:
        model = User
        fields = [
            'id', 
            'name', 
            'connection_status', 
            'major',
            'year',
            'bio',
        ]

class PrivateUserSerializer(UserSerializer):
    """Encapsulates a serializer that can serialize or deserialize a User with contact details."""

    class Meta:
        model = User
        fields = [
            'id', 
            'name', 
            'connection_status', 
            'major',
            'year',
            'nus_email', 
            'telegram_id', 
            'phone_number', 
            'bio',
        ]

