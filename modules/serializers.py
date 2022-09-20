from rest_framework import serializers

from users.models import Enrolment

from .models import Module

class ModuleSerializer(serializers.ModelSerializer):
    is_enrolled = serializers.SerializerMethodField()

    def get_is_enrolled(self, obj):
        user = self.context.get('user')
        return Enrolment.objects.filter(user=user, module=obj).exists()
    class Meta:
        model = Module
        fields = ('title', 'module_code', 'is_enrolled')