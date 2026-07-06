from django.contrib.auth.models import AbstractUser 
from django.contrib.auth.base_user import BaseUserManager
from django.db import models


# bikin CustomManager biar gak rewel
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('email wajib diisi!')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
        

class User(AbstractUser):
    
    
    username = None
    email = models.EmailField(unique=True, max_length=255)
    
    objects = CustomUserManager() #type:ignore
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    
    