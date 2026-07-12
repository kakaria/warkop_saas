from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


# bikin CustomManager biar gak rewel
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("email wajib diisi bang!")
        email = self.normalize_email(email)

        # panggil model User (self.model adalah model yang bakal manggil CustomUserManager)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(
            using=self._db
        )  # self._db biar ngatur db apa yang dipake (ini default, karena cuma make postgres)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):

    username = None
    email = models.EmailField(unique=True, max_length=255)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
