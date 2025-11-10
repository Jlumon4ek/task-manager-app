from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from common.mixins import TimestampMixin

class User(AbstractBaseUser, TimestampMixin):
    email = models.EmailField(
        unique=True,
        max_length=255,
        verbose_name='Email Address'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        db_table = 'users'

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email
