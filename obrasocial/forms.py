from django import forms

from .models import ObraSocial,PlanObraSocial



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
        
class PlanObraSocialForm(forms.ModelForm):

    class Meta:

        model = PlanObraSocial

        fields = (
            "codigo",
            "nombre",
            "observaciones",
            "orden",
            "activo",
        )

        widgets = {

            "codigo": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej.: 210"
            }),

            "nombre": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Nombre del plan"
            }),

            "observaciones": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),

            "orden": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 0
            }),

            "activo": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

        }

    def __init__(self, *args, obra_social=None, **kwargs):

        self.obra_social = obra_social

        super().__init__(*args, **kwargs)

    def clean_codigo(self):

        codigo = self.cleaned_data["codigo"]

        codigo = codigo.strip().upper()

        if self.obra_social:

            existe = PlanObraSocial.objects.filter(
                obra_social=self.obra_social,
                codigo=codigo
            )

            if self.instance.pk:

                existe = existe.exclude(pk=self.instance.pk)

            if existe.exists():

                raise forms.ValidationError(
                    "Ya existe un plan con ese código."
                )

        return codigo

    def clean_nombre(self):

        nombre = self.cleaned_data["nombre"].strip()

        if not nombre:

            raise forms.ValidationError(
                "Debe ingresar un nombre."
            )

        return nombre