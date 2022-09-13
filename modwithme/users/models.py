from datetime import datetime
from django.db import models
from modwithme.modules.models import Module

class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    nus_email = models.EmailField(unique=True)
    telegram_id = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    year = models.IntegerField(default=1)
    major = models.CharField(max_length=20)
    bio = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name

class Enrolment(models.Model):
    LOOKING = 'LF'
    WILLING = 'WH'
    NOT_LOOKING = 'NL'

    STATUS_CHOICES = [
        (LOOKING, 'Looking for a friend'),
        (WILLING, 'Willing to help'),
        (NOT_LOOKING, 'Not looking'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default=LOOKING,
    )

class Connection(models.Model):
    ACCEPTED = 'AC'
    PENDING = 'PD'
    REJECTED = 'RJ'

    CONNECTION_STATUS = [
        (ACCEPTED, 'Accepted'),
        (PENDING, 'Pending'),
        (REJECTED, 'Rejected'),
    ]

    id = models.AutoField(primary_key=True)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name= 'requester')
    accepter = models.ForeignKey(User, on_delete=models.CASCADE, related_name= 'accepter')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    dateTime = models.DateTimeField()
    status = models.CharField(
        max_length=2,
        choices=CONNECTION_STATUS,
        default=PENDING,
    )

    
