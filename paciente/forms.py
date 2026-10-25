from django import forms
from paciente.models import Paciente
from obrasocial.models import PlanObraSocial
from django.db import models


class PacienteForm(forms.ModelForm):

    class Meta:
        model = Paciente

        fields = [
            'dni',
            'nombre',
            'apellido',
            'fecha_nacimiento',
            'telefono',
            'sexo',
            'email',
            'direccion',
            'observaciones',
            'obrasocial',
            'plan_obra_social',
            'numero_afiliado',
        ]

        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'nombre': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'apellido': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'sexo': forms.Select(attrs={
                'class': 'form-select'
            }),

            'telefono': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),

            'direccion': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),

            'obrasocial': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_obrasocial',
            }),

            'plan_obra_social': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_plan_obra_social',
            }),

            'numero_afiliado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingrese el número de afiliado'
            }),
        }

    # ==================================================
    # INICIALIZAR PLANES SEGÚN OBRA SOCIAL
    # ==================================================


    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # ==========================================
        # CONFIGURACIÓN DEL CAMPO PLAN
        # ==========================================

        self.fields["plan_obra_social"].required = False

        self.fields["plan_obra_social"].empty_label = (
            "Seleccione un plan"
        )

        self.fields["plan_obra_social"].queryset = (
            PlanObraSocial.objects.none()
        )

        # ==========================================
        # INICIALIZAR OBRA SOCIAL
        # ==========================================

        obra_social_id = None

        # Cuando se envía el formulario (POST)
        if self.is_bound:

            obra_social_id = self.data.get(
                self.add_prefix("obrasocial")
            )

        # Cuando se está editando un paciente (GET)
        elif self.instance and self.instance.pk:

            obra_social_id = self.instance.obrasocial_id

        # ==========================================
        # CARGAR PLANES DE LA OBRA SOCIAL
        # ==========================================

        if obra_social_id:

            try:

                planes = PlanObraSocial.objects.filter(
                    obra_social_id=obra_social_id,
                    activo=True
                )

                # Conservar el plan actual al editar,
                # aunque haya sido desactivado.
                if (
                    self.instance
                    and self.instance.pk
                    and self.instance.plan_obra_social_id
                    and str(self.instance.obrasocial_id)
                        == str(obra_social_id)
                ):

                    planes = PlanObraSocial.objects.filter(
                        obra_social_id=obra_social_id
                    ).filter(
                        models.Q(activo=True)
                        | models.Q(
                            pk=self.instance.plan_obra_social_id
                        )
                    )

                self.fields["plan_obra_social"].queryset = (
                    planes.order_by(
                        "orden",
                        "codigo",
                        "nombre"
                    )
                )

            except (ValueError, TypeError):

                pass
    
   # ==================================================
    # VALIDAR PLAN SELECCIONADO
    # ==================================================

    def clean(self):

        cleaned_data = super().clean()

        obra_social = cleaned_data.get('obrasocial')

        plan = cleaned_data.get('plan_obra_social')

        if plan and obra_social:

            if plan.obra_social_id != obra_social.id:

                self.add_error(
                    'plan_obra_social',
                    'El plan seleccionado no pertenece '
                    'a la obra social indicada.'
                )

        return cleaned_data


class BusquedaPacienteForm(forms.Form):

    dni = forms.IntegerField(
        label='Ingrese el DNI'
    )