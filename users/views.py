from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, VerificationCode
from .serializers import RegisterSerializer

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        nus_email = request.data.get('nus_email')
        nus_email_is_already_used = User.objects.filter(nus_email=nus_email).exists()

        if nus_email_is_already_used:
            return Response({
                'error_code': 1,
                'error_message': 'Email is already in use.'
            })

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        verification_code = VerificationCode.objects.create(user=user)
        verification_code.send()

        return Response()

class OtpVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        nus_email = request.data.get('nus_email')
        code = request.data.get('otp')

        user = User.objects.filter(nus_email=nus_email).first()
        verification_code = VerificationCode.objects.filter(user__nus_email=nus_email, code=code).first()

        if user is None:
            return Response()
        elif verification_code is None:
            return Response({
                'error_code': 1,
                'error_message': 'Wrong OTP.'
            })
        elif verification_code.is_expired():
            return Response({
                'error_code': 2,
                'error_message': 'OTP has expired.'
            })
        
        user.is_verified = True
        user.save()
        verification_code.delete()

        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })

class OtpSendView(APIView):
    def post(self, request, *args, **kwargs):
        nus_email = request.data.get('nus_email')
        user = User.objects.filter(nus_email=nus_email).first()
        verification_code = VerificationCode.objects.filter(user__nus_email=nus_email).first()

        if not user:
            return Response()
        elif user.is_verified:
            return Response()
        elif verification_code and not verification_code.is_expired():
            remaining_time = round(verification_code.remaining_time())
            return Response({
                'error_code': 1,
                'error_message': f'Please wait {remaining_time} seconds before re-sending the OTP.'
            })
        elif verification_code:
            verification_code.delete()
        
        verification_code = VerificationCode.objects.create(user=user)
        verification_code.send()

        return Response()

class LoginView(TokenObtainPairView):
    """Takes a set of user credentials. 
    If the credentials are valid and the user's NUS Email is verified, 
    returns an access and refresh JSON web token pair."""

    serializer_class = TokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        nus_email = request.data.get('nus_email')
        password = request.data.get('password')
        
        user = authenticate(request, nus_email=nus_email, password=password)

        if not user:
            return Response({
                'error_code': 1,
                'error_message': 'Email and/or password is incorrect.'
            })

        return super().post(request, *args, **kwargs)
