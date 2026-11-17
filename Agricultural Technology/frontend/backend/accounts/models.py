from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, role='BUYER', **extra_fields):
        if not phone_number:
            raise ValueError('ফোন নম্বর আবশ্যক!')

        user = self.model(phone_number=phone_number, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser-এ is_staff=True থাকতে হবে।')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser-এ is_superuser=True থাকতে হবে।')

        return self.create_user(phone_number, password, role='ADMIN', **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('FARMER', 'Farmer'),
        ('BUYER', 'Commercial Buyer'),
        ('DRIVER', 'Driver'),
        ('ADMIN', 'Admin'),
    )
    phone_number = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=100)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='BUYER')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['full_name']
    objects = CustomUserManager()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    business_name = models.CharField(max_length=150, blank=True, null=True)
    address = models.TextField()
    latitude = models.FloatField(default=23.8103)   # ঢাকা ডিফল্ট
    longitude = models.FloatField(default=90.4125)

    def __str__(self):
        return f"{self.user.full_name} ({self.user.role})"
