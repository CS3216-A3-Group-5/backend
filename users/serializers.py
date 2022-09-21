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

class SimpleUserSerializer(serializers.ModelSerializer):
    """Encapsulates a serializer that can serialize or deserialize a User with limited details."""
    user_status = serializers.SerializerMethodField()  # the user's enrolment status in a module
    connection_status = serializers.SerializerMethodField()  # the user's connection status with request.user
    thumbnail_pic = serializers.ImageField(read_only=True, use_url=True, required=False, allow_empty_file=True)

    class Meta:
        model = User
        fields = [
            'id', 
            'name',
            'thumbnail_pic',
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

class PrivateUserSerializer(SimpleUserSerializer):
    """Encapsulates a serializer that can serialize or deserialize a User with contact details."""
    profile_pic = serializers.ImageField(read_only=True, use_url=True, required=False, allow_empty_file=True)

    class Meta:
        model = User
        fields = [
            'id', 
            'name', 
            'thumbnail_pic',
            'connection_status', 
            'major',
            'year',
            'profile_pic',
            'nus_email', 
            'telegram_id', 
            'phone_number', 
            'bio',
        ]

class UserSerializer(PrivateUserSerializer):
    """Encapsulates a serializer that can serialize or deserialize a User without contact details."""
    nus_email = serializers.SerializerMethodField()
    telegram_id = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 
            'name', 
            'thumbnail_pic',
            'connection_status', 
            'major',
            'year',
            'profile_pic',
            'nus_email', 
            'telegram_id', 
            'phone_number', 
            'bio',
        ]
    
    def get_nus_email(self, obj):
        return ''
    
    def get_telegram_id(self, obj):
        return ''
    
    def get_phone_number(self, obj):
        return ''

class ProfilePictureSerializer(serializers.ModelSerializer):
    profile_pic = serializers.ImageField(max_length=None, use_url=True, required=False, allow_empty_file=True)
    
    class Meta:
        model = User
        fields = ['profile_pic',]

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
    