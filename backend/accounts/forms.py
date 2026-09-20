from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import ClientUser


class ClientSignupForm(forms.Form):
    full_name = forms.CharField(max_length=300)
    email = forms.EmailField()
    referral_code = forms.CharField(max_length=100)
    password = forms.CharField(min_length=8, widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if ClientUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        email = self.cleaned_data.get("email", "")
        full_name = self.cleaned_data.get("full_name", "")
        candidate = ClientUser(username=email, email=email, first_name=full_name)
        try:
            validate_password(password, candidate)
        except ValidationError as error:
            raise forms.ValidationError(error.messages)
        return password


class ClientLoginForm(forms.Form):
    username = forms.CharField(max_length=254)
    password = forms.CharField(widget=forms.PasswordInput)
