from rest_framework import permissions

class IsSelf(permissions.BasePermission):
    """
    Custom permission to only allow request.user to access.
    """

    def has_object_permission(self, request, view, obj):
        return obj == request.user