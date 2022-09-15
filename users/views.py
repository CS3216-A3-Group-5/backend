from rest_framework_simplejwt.views import TokenObtainPairView as JwtTokenObtainPairView

from .serializers import TokenObtainPairSerializer

class TokenObtainPairView(JwtTokenObtainPairView):
    """Custom TokenObtainPairView. 
    Takes a set of user credentials. 
    If the credentials are valid and the user's NUS Email is verified, 
    returns an access and refresh JSON web token pair."""

    serializer_class = TokenObtainPairSerializer