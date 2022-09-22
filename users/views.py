from urllib import response
from django.db.models import Q
from django.contrib.auth import authenticate
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from modules import serializers

from .models import Connection_Status, User, VerificationCode, Enrolment, Connection
from .serializers import ConnectionSerializer, RegisterSerializer, UserSerializer
from .permissions import IsSelf
from .serializers import RegisterSerializer, UserSerializer, PrivateUserSerializer, ProfilePictureSerializer
from modules.serializers import ModuleSerializer
from modules.models import Module
from modules.views import User_Status

class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        nus_email = request.data.get('nus_email')
        user = User.objects.filter(nus_email=nus_email).first()
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'

        if user and user.is_verified:
            response = Response({
                'error_code': 1,
                'error_message': 'Email is already in use.'
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response
        elif user and not user.is_verified:
            return response

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        verification_code = VerificationCode.objects.create(user=user)
        verification_code.send()

        return response

class OtpVerifyView(APIView):
    def post(self, request, *args, **kwargs):
        nus_email = request.data.get('nus_email')
        code = request.data.get('otp')

        user = User.objects.filter(nus_email=nus_email).first()
        verification_code = VerificationCode.objects.filter(user__nus_email=nus_email, code=code).first()

        if user is None:
            response = Response()
            response['Access-Control-Allow-Origin'] = '*'
            return response
        elif verification_code is None:
            response = Response({
                'error_code': 1,
                'error_message': 'Wrong OTP.'
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response
        elif verification_code.is_expired():
            response = Response({
                'error_code': 2,
                'error_message': 'OTP has expired.'
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response
        
        user.is_verified = True
        user.save()
        verification_code.delete()

        refresh = RefreshToken.for_user(user)
        
        response = Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        })
        response['Access-Control-Allow-Origin'] = '*'
        return response

class OtpSendView(APIView):
    def post(self, request, *args, **kwargs):
        nus_email = request.data.get('nus_email')
        user = User.objects.filter(nus_email=nus_email).first()
        verification_code = VerificationCode.objects.filter(user__nus_email=nus_email).first()

        if not user:
            response = Response()
            response['Access-Control-Allow-Origin'] = '*'
            return response
        elif user.is_verified:
            response = Response()
            response['Access-Control-Allow-Origin'] = '*'
            return response
        elif verification_code and not verification_code.can_resend():
            remaining_time = round(verification_code.remaining_time_to_resend())
            response = Response({
                'error_code': 1,
                'error_message': f'Please wait {remaining_time} seconds before re-sending the OTP.'
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response
        elif verification_code:
            verification_code.delete()
        
        verification_code = VerificationCode.objects.create(user=user)
        verification_code.send()

        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        return response

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
            response = Response({
                'error_code': 1,
                'error_message': 'Email and/or password is incorrect.'
            })
            response['Access-Control-Allow-Origin'] = '*'
            return response

        response = super().post(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        return response

class StudentModulesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        search_query = request.query_params.get('q')
        paginator = PageNumberPagination()
        
        enrolment = Enrolment.objects.filter(user__exact=request.user).select_related('module')

        modules = Module.objects.filter(id__in=enrolment.values('module'))

        if search_query:
            modules = modules.filter(Q(title__icontains=search_query) | Q(module_code__icontains=search_query))
        
        queryset = paginator.paginate_queryset(modules, request)
        serializer = ModuleSerializer(queryset, many=True, context={'user': request.user})
        response = Response(serializer.data)
        response['Access-Control-Allow-Origin'] = '*'
        return response

class StudentSelfView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsSelf]

    def get(self, request):
        user = request.user
        serializer = PrivateUserSerializer(user)
        response = Response(serializer.data)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def put(self, request):
        user = request.user
        serializer = PrivateUserSerializer(user, data=request.data)
        if not serializer.is_valid():
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        
        serializer.save()
        response = Response(serializer.data)
        response['Access-Control-Allow-Origin'] = '*'
        return response

class StudentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        user = request.user
        target_user = User.objects.filter(id=id).first()

        if target_user is None:
            return Response("Invalid user id", status=status.HTTP_404_NOT_FOUND)
        elif user == target_user:
            serializer = PrivateUserSerializer(user)
        elif user.is_connected(target_user):
            serializer = PrivateUserSerializer(target_user, context={'user': request.user})
        else:
            serializer = UserSerializer(target_user, context={'user': request.user})

        response = Response(serializer.data)
        response['Access-Control-Allow-Origin'] = '*'
        return response

class StudentEnrollView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        self.http_method_names.append("post")
        user = request.user
        data = request.data

        try:
            obj = data
            module_code = obj["module_code"]
            module = Module.objects.get(module_code__iexact=module_code)
            user_status = User_Status(0).name

            print(Enrolment.objects.filter(user=user, module=module))

            if Enrolment.objects.filter(user=user, module=module).exists():
                response = Response('User is already enrolled in this module', status=status.HTTP_405_METHOD_NOT_ALLOWED)
                response['Access-Control-Allow-Origin'] = '*'
                return response
            
            enrolment = Enrolment(user=user, module=module, status=user_status)
            enrolment.save()

            response = Response("Successfully enrolled")
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as e:
            print(e)
            response = Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
            response['Access-Control-Allow-Origin'] = '*'
            return response

    def delete(self, request=None):
        user = request.user
        data = request.data

        try:
            obj = data
            module_code = obj["module_code"]
            module = Module.objects.get(module_code__iexact=module_code)

            enrolment = Enrolment.objects.filter(user=user, module=module)

            if not enrolment.exists:
                response = Response('User is not enrolled in this module', status=status.HTTP_405_METHOD_NOT_ALLOWED)
                response['Access-Control-Allow-Origin'] = '*'
                return response
            
            enrolment.delete()

            response = Response("Successfully deleted")
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except:
            response = Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
            response['Access-Control-Allow-Origin'] = '*'
            return response

class ModuleStatusView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, module_code, format=None):
        user = request.user        
        
        enrolment = Enrolment.objects.filter(user=user, module__module_code=module_code).first()

        if enrolment is None:
            return Response({'status': 3})
        
        return Response({'status': User_Status[enrolment.status].value})

    def put(self, request, module_code, format=None):
        user = request.user
        data = request.data

        try:
            obj = data
            module = Module.objects.get(module_code__iexact=module_code)
            user_status = obj["status"]
            user_status = User_Status(user_status).name
            
            enrolment = Enrolment.objects.filter(user=user, module=module)
            if not enrolment.exists():
                response = Response('User is not enrolled in this module', status=status.HTTP_405_METHOD_NOT_ALLOWED)
                response['Access-Control-Allow-Origin'] = '*'
                return response
            
            enrolment.update(status=user_status)

            response = Response("Successfully updated status")
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as e:
            print(e)
            response = Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
            response['Access-Control-Allow-Origin'] = '*'
            return response

class ProfilePictureView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def get(self, request):
        user = request.user
        serializer = ProfilePictureSerializer(user)
        response = Response(serializer.data)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def post(self, request):
        user = request.user
        serializer = ProfilePictureSerializer(user, data=request.data)
        if not serializer.is_valid():
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            response['Access-Control-Allow-Origin'] = '*'
            return response
        
        serializer.save()
        response = Response(serializer.data, status=status.HTTP_200_OK)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def delete(self, request):
        user = request.user
        user.profile_pic = None
        user.save()
        response = Response()
        response['Access-Control-Allow-Origin'] = '*'
        return response

class UserConnectionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        connections = Connection.objects.filter(Q(accepter=user) | Q(requester=user), ~Q(status=Connection_Status['RJ'].value))

        type = request.query_params.get('type')
        module_query = request.query_params.get('module_code')

        if type and type == '0':
            connections = connections.filter(accepter=user, status='PD')
        elif type and type == '1':
            connections = connections.filter(requester=user, status='PD')
        elif type and type == '2':
            connections = connections.filter(status='AC')

        if module_query:
            enrolments = Enrolment.objects.filter(Q(module__module_code__icontains=module_query) | Q(module__title__icontains=module_query))
            users = enrolments.values_list('user', flat=True).distinct()
            connections = connections.filter(Q(requester=user, accepter__in=users) | Q(accepter=user, requester__in=users))
        
        connections = connections.order_by('creation_time')
        
        serializer = ConnectionSerializer(connections, many=True, context={'user': user})
        response = Response(serializer.data)
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def post(self, request, format=None):
        user = request.user
        data = request.data

        try:
            obj = data
            module_code = obj["module_code"]
            module = Module.objects.get(module_code__iexact=module_code)
            other_user_id = obj["other_user"]
            other_user = User.objects.get(id=other_user_id)


            connection = Connection.objects.filter(Q(requester=user, accepter=other_user) | Q(requester=other_user, accepter=user))
            if connection.exists():
                response = Response('A connection between these 2 users already exists.', status=status.HTTP_405_METHOD_NOT_ALLOWED)
                response['Access-Control-Allow-Origin'] = '*'
                return response
            elif user.id == other_user_id:
                response = Response('Cannot connect user with themselves', status=status.HTTP_405_METHOD_NOT_ALLOWED)
                response['Access-Control-Allow-Origin'] = '*'
                return response

            connection = Connection(requester=user, accepter=other_user, module=module, status='PD')
            connection.save()
            serializer = ConnectionSerializer(connection, context={'user': user})
            response = Response(serializer.data)
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as e:
            print(e)
            response = Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
            response['Access-Control-Allow-Origin'] = '*'
            return response
    
    def put(self, request, format=None):
        user = request.user
        data = request.data

        try:
            obj = data
            connection_id = obj["id"]
            new_status = Connection_Status(int(obj["status"])).name 
            

            connection = Connection.objects.filter(id=connection_id)
            if not connection.exists():
                response = Response('No match for connection id', status=status.HTTP_404_NOT_FOUND)
                response['Access-Control-Allow-Origin'] = '*'
                return response
            elif not connection.filter(Q(requester=user) | Q(accepter=user)).exists():
                response = Response('User not involved in connection.', status=status.HTTP_401_UNAUTHORIZED)
                response['Access-Control-Allow-Origin'] = '*'
                return response
            elif connection.filter(requester=user).exists() and new_status == Connection_Status.AC.value:
                response = Response('Requester cannot accept connection', status=status.HTTP_405_METHOD_NOT_ALLOWED)
                response['Access-Control-Allow-Origin'] = '*'
                return response

            if new_status == 0:
                connection.delete()
            else:
                connection.update(status=new_status)

            response = Response("Successfully updated status")
            response['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as e:
            print(e)
            response = Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)
            response['Access-Control-Allow-Origin'] = '*'
            return response
