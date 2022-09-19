from rest_framework import generics
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView as JwtTokenObtainPairView

from .models import User
from .serializers import TokenObtainPairSerializer, RegisterSerializer

class TokenObtainPairView(JwtTokenObtainPairView):
    """Custom TokenObtainPairView. 
    Takes a set of user credentials. 
    If the credentials are valid and the user's NUS Email is verified, 
    returns an access and refresh JSON web token pair."""

    serializer_class = TokenObtainPairSerializer

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        nus_email = request.data['nus_email']
        nus_email_is_already_used = User.objects.filter(nus_email=nus_email).exists()

        if nus_email_is_already_used:
            return Response({
                'error_code': 1,
                'error_message': 'Email is already in use.'
            })

        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response()