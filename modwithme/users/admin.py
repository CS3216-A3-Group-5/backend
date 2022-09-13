from django.contrib import admin
from .models import User, Enrolment, Connection

# Register your models here.
admin.site.register(User)
admin.site.register(Enrolment)
admin.site.register(Connection)
