from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Articulo


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
        fields =  ['username', 'email', 'password1', 'password2']

    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Usuario',
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email',
    }))
    password1= forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Contraseña',
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Repetir Contraseña',
    }))

    # Comprobar correo electrónico único
    # El correo electrónico existe y la cuenta está activa -> correo_ya_registrado
    # El correo electrónico existe y la cuenta no está activa -> eliminar la cuenta anterior y registrar una nueva
    def clean_email(self):
        email_recibido = self.cleaned_data.get("email")
        correo_ya_registrado = User.objects.filter(email = email_recibido).exists()
        user_es_activo = User.objects.filter(email = email_recibido, is_active = 1)
        if correo_ya_registrado and user_es_activo:
            raise forms.ValidationError("Correo electrónico ya registrado.")
        elif correo_ya_registrado:
            User.objects.filter(email = email_recibido).delete()

        return email_recibido