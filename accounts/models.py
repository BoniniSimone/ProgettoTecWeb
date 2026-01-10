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
    user = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="newsletter_subscriptions",
    )
    is_active = models.BooleanField(default=True)
    consent_at = models.DateTimeField(default=timezone.now)

    # opzionale (ma utile): fonte e auditing minimo
    source = models.CharField(max_length=50, blank=True)  # es. "checkout", "footer", "admin"

    def __str__(self):
        return f"{self.email} ({'active' if self.is_active else 'inactive'})"

