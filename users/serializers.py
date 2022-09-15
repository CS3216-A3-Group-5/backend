from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer

from .models import User

class TokenObtainPairSerializer(JwtTokenObtainPairSerializer):
    def validate(self, attrs):
        nus_email = attrs.get('nus_email')
        user = User.objects.filter(nus_email=nus_email).first()
        
        if not user.is_verified:
            return None

        return super().validate(attrs)