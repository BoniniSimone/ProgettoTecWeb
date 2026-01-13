from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=30, blank=True)
    socio = models.BooleanField(default=False)

    def __str__(self):
        return self.username or self.email
    


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email

