from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Connections, User

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'nus_email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['nus_email'], validated_data['password'])

        return user

class SimpleUserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50, source='user.username')
    user_status = serializers.SerializerMethodField()  # based on module
    connection_status = serializers.SerializerMethodField()  #based on module and user token

    def get_user_status(self, obj):
        if obj.status == 'LF':
            return 1
        elif obj.status == 'WH':
            return 2
        else:
            return 0
        
    def get_connection_status(self, obj):
        # get Connections table filtered by requester or accepter being user making api request
        # for each user, check if in this filtered table
        # if in table, return connection status
        # else no connection
        user = None
        user = self.context.get('user')
        module_code = self.context.get('module_code')

        queryset = Connections.objects.filter(Q(requester=user) | Q(accepter=user), module__module_code__iexact=module_code)

        record = queryset.get(Q(requester__exact=obj.user) | Q(accepter__exact=obj.user))
        if record.status == 'AC':
            return 2
        elif record.status == 'PD':
            return 1
        else:
            return 0

        
