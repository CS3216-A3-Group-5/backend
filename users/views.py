from django.db.models import Q

from rest_framework_simplejwt.views import TokenObtainPairView as JwtTokenObtainPairView
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from modules.serializers import ModuleSerializer

from .serializers import TokenObtainPairSerializer, UserSerializer

from modules.models import Module
from .models import User, Enrolment, Connections

class TokenObtainPairView(JwtTokenObtainPairView):
    """Custom TokenObtainPairView. 
    Takes a set of user credentials. 
    If the credentials are valid and the user's NUS Email is verified, 
    returns an access and refresh JSON web token pair."""

    serializer_class = TokenObtainPairSerializer

class StudentModulesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        search_query = request.query_params.get('q')
        paginator = PageNumberPagination()
        
        enrolment = Enrolment.objects.filter(user__exact=request.user).select_related('module')

        modules = Module.objects.filter(id__in=enrolment.values('module'))

        if search_query is not None:
            modules = modules.filter(Q(title__icontains=search_query) | Q(module_code__icontains=search_query))
        
        queryset = paginator.paginate_queryset(modules, request)
        serializer = ModuleSerializer(queryset, many=True)
        return Response(serializer.data)

class StudentSelfView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        
        user = request.user
        
        serializer = UserSerializer(user)
        return Response(serializer.data)

class StudentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        user = request.user
        try:
            target = User.objects.get(id__exact=id)
        except:
            return Response("Invalid user id", status=status.HTTP_404_NOT_FOUND)

        if user == target:
            serializer = UserSerializer(user)
            return Response(serializer.data)

        if not Connections.objects.filter(Q(requester=user, accepter=target) | Q(requester=target, accepter=user)).exists():
            return Response("No connection with this user", status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = UserSerializer(target)
        return Response(serializer.data)