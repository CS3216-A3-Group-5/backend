from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

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

class Connections(models.Model):
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
    dateTime = models.DateTimeField()
    status = models.CharField(
        max_length=2,
        choices=CONNECTION_STATUS,
        default=PENDING,
    )

    
