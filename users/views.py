from django.db.models import Q
from django.contrib.auth import authenticate
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, VerificationCode, Enrolment, Connection
from .serializers import RegisterSerializer, UserSerializer, PrivateUserSerializer
from modules.serializers import ModuleSerializer
from modules.models import Module
from modules.views import User_Status

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
        serializer = ModuleSerializer(queryset, many=True, context={'user': request.user})
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
        target_user = User.objects.filter(id=id).first()

        if target_user is None:
            return Response("Invalid user id", status=status.HTTP_404_NOT_FOUND)
        elif user == target_user:
            serializer = PrivateUserSerializer(user)
        elif user.is_connected(target_user):
            serializer = PrivateUserSerializer(target_user, context={'user': request.user})
        else:
            serializer = UserSerializer(target_user, context={'user': request.user})

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
            module = Module.objects.get(module_code__iexact=module_code)
            user_status = User_Status(0).name

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
            module = Module.objects.get(module_code__iexact=module_code)

            enrolment = Enrolment.objects.filter(user=user, module=module)

            if not enrolment.exists:
                return Response('User is not enrolled in this module', status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
            enrolment.delete()

            return Response("Successfully deleted")

        except:
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)

class ModuleStatusView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, format=None):
        user = request.user
        data = request.data

        try:
            obj = data
            module_code = obj["module_code"]
            module = Module.objects.get(module_code__iexact=module_code)
            user_status = obj["status"]
            user_status = User_Status(user_status).name
            
            enrolment = Enrolment.objects.filter(user=user, module=module)
            if not enrolment.exists():
                return Response('User is not enrolled in this module', status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
            enrolment.update(status=user_status)

            return Response("Successfully updated status")

        except Exception as e:
            print(e)
            return Response("Invalid request", status=status.HTTP_400_BAD_REQUEST)