from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from django.contrib.auth.forms import AuthenticationForm

class NewsletterSubscribeForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Inserisci la tua email",
            "required": True,
        }),
    )

    def clean_email(self):
        # normalizzazione: riduce edge-case e rende il confronto coerente
        return self.cleaned_data["email"].strip().lower()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "phone_number", "password1", "password2")


class BootstrapAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
