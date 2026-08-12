from django import forms

from .models import ObraSocial,PlanObraSocial,PrestacionPlan



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
            
            "es_particular",
            "usa_planes",
            
           

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
            "es_particular": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

            "usa_planes": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),

        }
    def clean(self):

        cleaned_data = super().clean()

        es_particular = cleaned_data.get(
            "es_particular"
        )

        usa_planes = cleaned_data.get(
            "usa_planes"
        )

        if es_particular and usa_planes:

            raise forms.ValidationError(

                "Una obra social marcada como Particular no puede utilizar planes."

            )

        return cleaned_data   
        
        
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
    
    
from django import forms

from caja.models import ConceptoFacturacion


class ConceptoFacturacionParticularForm(forms.ModelForm):

    class Meta:
        model = ConceptoFacturacion

        fields = [
            "importe_particular",
            "tipo_concepto",
            "porcentaje_iva",
            "tipo_calculo",
            "porcentaje_medico",
            "porcentaje_consultorio",
            "honorario_fijo_medico",
            "proveedor",
            "importe_proveedor",
            "activo",
        ]

        widgets = {

            "importe_particular": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "tipo_concepto": forms.Select(attrs={
                "class": "form-select",
            }),

            "porcentaje_iva": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "tipo_calculo": forms.Select(attrs={
                "class": "form-select",
            }),

            "porcentaje_medico": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "porcentaje_consultorio": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "honorario_fijo_medico": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "proveedor": forms.Select(attrs={
                "class": "form-select",
            }),

            "importe_proveedor": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "activo": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

        labels = {
            "importe_particular": "Precio Particular",
            "tipo_concepto": "Tipo de prestación",
            "porcentaje_iva": "IVA (%)",
            "tipo_calculo": "Tipo de cálculo",
            "porcentaje_medico": "Porcentaje Médico (%)",
            "porcentaje_consultorio": "Porcentaje Consultorio (%)",
            "honorario_fijo_medico": "Honorario fijo médico",
            "proveedor": "Proveedor",
            "importe_proveedor": "Importe proveedor",
            "activo": "Concepto activo",
        }
        
class PrestacionPlanForm(forms.ModelForm):

    class Meta:

        model = PrestacionPlan

        fields = [
            "valor",
            "porcentaje_iva",
            "tipo_calculo",
            "porcentaje_medico",
            "porcentaje_consultorio",
            "honorario_fijo_medico",
            "tipo_concepto",
            "proveedor",
            "importe_proveedor",
            "estado",
        ]

        widgets = {

            "valor": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "porcentaje_iva": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "tipo_calculo": forms.Select(attrs={
                "class": "form-select"
            }),

            "porcentaje_medico": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "porcentaje_consultorio": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "honorario_fijo_medico": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "tipo_concepto": forms.Select(attrs={
                "class": "form-select"
            }),

            "proveedor": forms.Select(attrs={
                "class": "form-select"
            }),

            "importe_proveedor": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "estado": forms.Select(attrs={
                "class": "form-select"
            }),
        }

        labels = {
            "valor": "Valor Convenio",
            "porcentaje_iva": "IVA (%)",
            "tipo_calculo": "Tipo de cálculo",
            "porcentaje_medico": "Porcentaje Médico",
            "porcentaje_consultorio": "Porcentaje Consultorio",
            "honorario_fijo_medico": "Honorario fijo médico",
            "tipo_concepto": "Tipo de prestación",
            "proveedor": "Proveedor",
            "importe_proveedor": "Importe proveedor",
            "estado": "Estado",
        }