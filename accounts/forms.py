from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.core.validators import RegexValidator


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9_\-]+$',
                message='Username may contain only letters, numbers, underscores, and hyphens.'
            )
        ]
    )
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "username",
        )


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "username",
        )