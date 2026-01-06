

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
class UserCreationFormWithEmail(UserCreationForm):
    email = forms.EmailField(required=True)
    help_texts=("Requerido 254 caracteres como maximo y debe ser un email valido ")
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'password1',
            'password2')
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("El email ya existe pruebe con otro")
        
        return email
        
        
 