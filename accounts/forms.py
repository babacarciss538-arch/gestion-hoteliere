from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from .models import User

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control glass-input',
            'placeholder': 'votre.email@hotel.com',
            'autocomplete': 'email',
            'required': True
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control glass-input',
            'placeholder': '••••••••••••',
            'autocomplete': 'current-password',
            'required': True
        })
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control glass-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control glass-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-control glass-input'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control glass-input'}),
        }
