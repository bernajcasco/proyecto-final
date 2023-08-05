from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Articulo , Comment


class ArticuloForm(forms.ModelForm):

    class Meta:
        model = Articulo
        fields = ['titulo', 'bajada', 'contenido',
                  'imagen', 'categoria', 'etiquetas']

        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'bajada': forms.TextInput(attrs={'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'etiquetas': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


class RegisterUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Usuario',
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Contraseña',
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Repetir Contraseña',
    }))

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']