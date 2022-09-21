import math, random
import os.path
from enum import Enum
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.utils import timezone
from io import BytesIO
from PIL import Image

from modules.models import Module
from modwithme.settings import THUMBNAIL_SIZE

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
    def profile_pic_image_path(instance, filename):
        return f'user/{instance.id}/{filename}'

    username = None
    name = models.CharField(max_length=50)
    nus_email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)
    telegram_id = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_pic = models.ImageField(upload_to=profile_pic_image_path, blank=True, null=True)
    thumbnail_pic = models.ImageField(upload_to=profile_pic_image_path, editable=False, blank=True, null=True)
    year = models.IntegerField(default=1)
    major = models.CharField(max_length=20)
    bio = models.TextField(blank=True)

    USERNAME_FIELD = 'nus_email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        self.create_thumbnail()

        super(User, self).save(*args, **kwargs)

    def create_thumbnail(self):
        if not self.profile_pic:
            self.thumbnail_pic = None
            return

        image = Image.open(self.profile_pic)
        image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
        thumbnail_name, thumbnail_extension = os.path.splitext(self.profile_pic.name)
        thumbnail_extension = thumbnail_extension.lower()
        thumbnail_filename = f'{thumbnail_name}_thumb{thumbnail_extension}'

        if thumbnail_extension in ['.jpg', '.jpeg']:
            FTYPE = 'JPEG'
        elif thumbnail_extension == '.gif':
            FTYPE = 'GIF'
        elif thumbnail_extension == '.png':
            FTYPE = 'PNG'
        else:
            raise Exception('Unable to create thumbnail. Profile picture must be in JPEG, PNG or GIF format.')

        # Save thumbnail to in-memory file as StringIO
        temp_thumbnail = BytesIO()
        image.save(temp_thumbnail, FTYPE)
        temp_thumbnail.seek(0)

        # set save=False, otherwise it will run in an infinite loop
        self.thumbnail_pic.save(thumbnail_filename, ContentFile(temp_thumbnail.read()), save=False)
        temp_thumbnail.close()

    def is_connected(self, other_user):
        return self.get_connection_status_with(other_user) == 2
    
    def get_connection_status_with(self, other_user):
        connection = Connection.objects.filter(Q(requester=self, accepter=other_user) | Q(requester=other_user, accepter=self)).first()
        if connection is None:
            return 0
        
        return Connection_Status[connection.status].value

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
    creation_time = models.DateTimeField(auto_now_add=True)
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
            'reply.no@engineer.com',
            [self.user.nus_email],
            fail_silently=False,
        )

    def elapsed_time(self):
        time_delta = timezone.now() - self.creation_time
        return time_delta.total_seconds()
    
    def is_expired(self):
        return self.elapsed_time() > settings.OTP_EXPIRATION_DURATION

    def can_resend(self):
        return self.elapsed_time() > settings.OTP_RESEND_DURATION

    def remaining_time_to_resend(self):
        return settings.OTP_RESEND_DURATION - self.elapsed_time()

    objects = VerificationCodeManager()