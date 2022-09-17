from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User, Enrolment, Connections

admin.site.register(Enrolment)
admin.site.register(Connections)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Custom UserAdmin for User model that uses nus_email instead of username."""

    fieldsets = (
        (None, {
            'fields': ('nus_email', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
                )
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Additional info', {
            'fields': ('is_verified',)
        })
    )
    list_display = ('nus_email', 'username', 'last_name', 'is_staff')
    search_fields = ('nus_email', 'first_name', 'last_name')
    ordering = ('nus_email',)