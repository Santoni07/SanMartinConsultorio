from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .form import UserCreationFormWithEmail
from django import forms

# Create your views here.

class SignUpView(CreateView):
    form_class =UserCreationFormWithEmail
    template_name = 'registration/signup.html'
    
    def get_success_url(self):
        return reverse_lazy('login') + '?register'
    
    def get_form(self, form_class=None):
        form = super(SignUpView, self).get_form()
        form.fields['username'].widget = forms.TextInput(attrs={'class':'form-control mb-2', 'placeholder':'Nombre'})
        form.fields['password1'].widget = forms.PasswordInput(attrs={'class':'form-control mb-2', 'placeholder':'Contraseña'})
        form.fields['password2'].widget = forms.PasswordInput(attrs={'class':'form-control mb-2', 'placeholder':'Repetir Contraseña'})
        form.fields['email'].widget = forms.EmailInput(attrs={'class':'form-control mb-2', 'placeholder':'Email'})
        return form
    

from django.views.decorators.cache import never_cache

@never_cache
def login_view(request):

    # 🔒 Si ya está logueado, no puede volver al login
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('core:IndexAdmin')

        if hasattr(request.user, 'medico'):
            return redirect('core:medico')

        return redirect('core:index')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        print("Intentando login con:", username)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            print("Login correcto")

            # 🔁 Redirección por rol
            if user.is_superuser or user.is_staff:
                return redirect('core:IndexAdmin')

            if hasattr(user, 'medico'):
                return redirect('core:medico')

            return redirect('core:index')

        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    return render(request, "registration/login.html")

def logout_view(request):
    logout(request)
    return redirect('core:index')