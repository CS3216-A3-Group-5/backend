from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as JwtTokenObtainPairSerializer

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