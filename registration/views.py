from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .form import UserCreationFormWithEmail,MiCuentaForm
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

from django.views.decorators.cache import never_cache


@never_cache
def login_view(request):

    # ==================================================
    # SI YA ESTÁ LOGUEADO
    # ==================================================

    if request.user.is_authenticated:

        try:

            perfil = request.user.perfilusuario

            if perfil.rol == 'GERENCIA':

                return redirect(
                    'gerencia:dashboard'
                )

        except Exception:
            pass


        if request.user.is_superuser or request.user.is_staff:

            return redirect(
                'core:IndexAdmin'
            )


        if hasattr(request.user, 'medico'):

            return redirect(
                'core:medico'
            )


        return redirect(
            'core:index'
        )


    # ==================================================
    # LOGIN
    # ==================================================

    if request.method == "POST":

        username = request.POST.get(
            "username"
        )

        password = request.POST.get(
            "password"
        )


        user = authenticate(
            request,
            username=username,
            password=password
        )


        if user is not None:

            # ==========================================
            # INICIAR SESIÓN
            # ==========================================

            login(
                request,
                user
            )


            # ==========================================
            # CONFIGURAR DURACIÓN DE SESIÓN
            # ==========================================
            #
            # MÉDICO:
            # No vence por inactividad.
            # Se cierra al cerrar el navegador.
            #
            # RESTO:
            # Mantiene los 20 minutos configurados
            # en settings.py.
            # ==========================================

            if hasattr(user, 'medico'):

                request.session.set_expiry(0)

            else:

                request.session.set_expiry(
                    20 * 60
                )


            # ==========================================
            # ASIGNAR CENTRO
            # ==========================================

            try:

                perfil = user.perfilusuario

                if perfil.centro_principal:

                    request.session[
                        'centro_id'
                    ] = perfil.centro_principal.id

                else:

                    primer_centro = (
                        perfil.centros.first()
                    )

                    if primer_centro:

                        request.session[
                            'centro_id'
                        ] = primer_centro.id


            except Exception as e:

                print(
                    "Error asignando centro:",
                    e
                )


            # ==========================================
            # REDIRECCIÓN GERENCIA
            # ==========================================

            try:

                perfil = user.perfilusuario

                if perfil.rol == 'GERENCIA':

                    return redirect(
                        'gerencia:dashboard'
                    )

            except Exception:
                pass


            # ==========================================
            # ADMINISTRADOR
            # ==========================================

            if (
                user.is_superuser or
                user.is_staff
            ):

                return redirect(
                    'core:IndexAdmin'
                )


            # ==========================================
            # MÉDICO
            # ==========================================

            if hasattr(user, 'medico'):

                return redirect(
                    'core:medico'
                )


            # ==========================================
            # RESTO DE USUARIOS
            # ==========================================

            return redirect(
                'core:index'
            )


        # ==========================================
        # LOGIN INCORRECTO
        # ==========================================

        else:

            messages.error(
                request,
                "Usuario o contraseña incorrectos."
            )


    return render(
        request,
        "registration/login.html"
    )


def logout_view(request):

    logout(request)

    return redirect(
        'core:index'
    )
def logout_view(request):
    logout(request)
    return redirect('core:index')


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def mis_datos(request):

    medico = getattr(request.user, "medico", None)

    if request.method == "POST":

        form = MiCuentaForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "El correo electrónico fue actualizado correctamente."
            )

    else:

        form = MiCuentaForm(
            instance=request.user
        )

    return render(
        request,
        "registration/mis_datos.html",
        {
            "usuario": request.user,
            "medico": medico,
            "form": form,
        }
    )
    
    
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash   

@login_required
def cambiar_password(request):

    if request.method == "POST":
        
      

        form = PasswordChangeForm(
            request.user,
            request.POST
        )

        if form.is_valid():

            user = form.save()

            update_session_auth_hash(
                request,
                user
            )

            messages.success(
                request,
                "La contraseña fue modificada correctamente."
            )

            return redirect("cambiar_password")
        else:
            print(form.errors)

    else:
        
        form = PasswordChangeForm(
            request.user
        )
    for field in form.fields.values():
        field.widget.attrs.update({
            "class": "form-control"
        })
    return render(
        request,
        "registration/cambiar_password.html",
        {
            "form": form
        }
    )