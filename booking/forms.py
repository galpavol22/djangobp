from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from .models import UserProfile

class SignupForm(forms.ModelForm):
    username = forms.CharField(
        min_length=3,
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Username',
            'minlength': '3',
        }),
        error_messages={
            'min_length': 'Meno musí mať aspoň 3 znaky.',
            'max_length': 'Meno môže mať najviac 30 znakov.'
        }
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email',
        })
    )

    phone = forms.CharField(
        min_length=3,
        max_length=15,
        validators=[RegexValidator(r'^\d+$', 'Telefón musí obsahovať len čísla.')],
        widget=forms.TextInput(attrs={
            'placeholder': 'Telefón',
            'minlength': '3',
        }),
        error_messages={
            'min_length': 'Telefón musí mať aspoň 3 číslice.',
            'max_length': 'Telefón môže mať najviac 15 číslic.'
        }
    )

    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Heslo',
            'minlength': '8',
        }),
        error_messages={
            'min_length': 'Heslo musí mať aspoň 8 znakov.'
        }
    )

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Používateľ s týmto menom už existuje.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Používateľ s týmto emailom už existuje.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if UserProfile.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Používateľ s týmto telefónnym číslom už existuje.")
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'phone': self.cleaned_data.get('phone')}
            )
        return user
