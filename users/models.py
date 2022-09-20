from enum import Enum
import math, random
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.mail import send_mail
from django.utils import timezone

from modules.models import Module

class UserManager(BaseUserManager):
    """A custom model manager for the custom User model that uses nus_email instead of username."""

    use_in_migrations = True

    def _create_user(self, nus_email, password, **extra_fields):
        """Creates and saves a User with the given nus_email and password."""

        if not nus_email:
            raise ValueError('NUS Email must be given')

        nus_email = self.normalize_email(nus_email)
        user = self.model(nus_email=nus_email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_user(self, nus_email, password=None, **extra_fields):
        """Creates and saves a regular User with the given nus_email and password."""

        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(nus_email, password, **extra_fields)

    def create_superuser(self, nus_email, password, **extra_fields):
        """Creates and saves a Superuser with the given nus_email and password."""
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(nus_email, password, **extra_fields)

class User(AbstractUser):
    username = None
    name = models.CharField(max_length=50)
    nus_email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    telegram_id = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    year = models.IntegerField(default=1)
    major = models.CharField(max_length=20)
    bio = models.TextField(blank=True)

    USERNAME_FIELD = 'nus_email'
    REQUIRED_FIELDS = []

    objects = UserManager()

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
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='outgoing_connections')
    accepter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incoming_connections')
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    creation_time = models.DateTimeField()
    status = models.CharField(
        max_length=2,
        choices=CONNECTION_STATUS,
        default=PENDING,
    )

class User_Status(Enum):
    NL = 0
    LF = 1
    WH = 2
class Connection_Status(Enum):
    RJ = 0
    PD = 1
    AC = 2
    
class VerificationCodeManager(models.Manager):
    @classmethod
    def generate_code(cls):
        digits = '0123456789'
        code = ''

        for i in range(6):
            code += digits[math.floor(random.random() * 10)]

        return int(code)

    def create(self, user):
        code = VerificationCodeManager.generate_code()
        return super().create(user=user, code=code)

class VerificationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification_code')
    code = models.PositiveSmallIntegerField()
    creation_time = models.DateTimeField(auto_now_add=True)

    def send(self):
        send_mail(
            'Your verification code for Mod With Me',
            f'Your verification code is: {self.code}',
            'no-reply@modwithme.com',
            [self.user.nus_email],
            fail_silently=False,
        )
    
    def remaining_time(self):
        return settings.OTP_EXPIRATION_DURATION - self.elapsed_time()

    def elapsed_time(self):
        time_delta = timezone.now() - self.creation_time
        return time_delta.total_seconds()
    
    def is_expired(self):
        return self.elapsed_time() > settings.OTP_EXPIRATION_DURATION

    objects = VerificationCodeManager()