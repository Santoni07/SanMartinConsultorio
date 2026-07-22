from django import forms

from .models import ObraSocial



class ObraSocialForm(forms.ModelForm):

    class Meta:

        model = ObraSocial

        fields = [

            "nombre",

            "sigla",

            "codigo",

            "cuit",

            "telefono",

            "email",

            "domicilio",

            "ciudad",

            "provincia",

            "observaciones",

            "activa",
            
           

            "sitio_web",
            "portal_prestadores",
            "portal_autorizaciones",
            "portal_afiliados",
            "cartilla_online",
            "credenciales_online",
            "observaciones_portal",

        ]
        

        widgets = {

            "nombre": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "sigla": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "codigo": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "cuit": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "telefono": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control"
            }),

            "domicilio": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "ciudad": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "provincia": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "observaciones": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "activa": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
            
             "sitio_web": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),

            "portal_prestadores": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),

            "portal_autorizaciones": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),

            "portal_afiliados": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),

            "cartilla_online": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),

            "credenciales_online": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "https://..."
            }),

            "observaciones_portal": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),

        }