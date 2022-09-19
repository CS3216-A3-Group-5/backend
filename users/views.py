import json
from django.db.models import Q

from rest_framework_simplejwt.views import TokenObtainPairView as JwtTokenObtainPairView
from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from modules.serializers import ModuleSerializer

from .serializers import TokenObtainPairSerializer, UserSerializer

from modules.models import Module
from .models import User, Enrolment, Connections
from modules.views import User_Status, Connection_Status

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

    # Error updating
    def put(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        


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

class StudentEnrollView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        self.http_method_names.append("post")
        user = request.user
        data = request.data

        try:
            obj = data
            module_code = obj["module_code"]
            module = Module.objects.get(module_code=module_code)
            user_status = obj["status"]
            user_status = User_Status(user_status).name

            if Enrolment.objects.filter(user=user, module=module).exists():
                return Response('User is already enrolled in this module', status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
            enrolment = Enrolment(user=user, module=module, status=user_status)
            enrolment.save()

            return Response("Successfully enrolled")

        except Exception as e:
            print(e)
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request=None):
        user = request.user
        data = request.data

        try:
            obj = data
            module_code = obj["module_code"]
            module = Module.objects.get(module_code=module_code)

            enrolment = Enrolment.objects.filter(user=user, module=module)

            if not enrolment.exists:
                return Response('User is not enrolled in this module', status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
            enrolment.delete()

            return Response("Successfully deleted")

        except:
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)

