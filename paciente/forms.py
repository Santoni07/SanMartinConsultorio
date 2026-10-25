
from django import forms
from django.db import models

from paciente.models import Paciente
from obrasocial.models import PlanObraSocial


# ==========================================================
# FUNCIONES COMPARTIDAS
# ==========================================================

def validar_dni_paciente(formulario):

    dni = formulario.cleaned_data["dni"]

    if (
        Paciente.objects
        .filter(dni=dni)
        .exclude(pk=formulario.instance.pk)
        .exists()
    ):
        raise forms.ValidationError(
            "Ya existe un paciente registrado con ese DNI."
        )

    return dni


def configurar_planes_obra_social(formulario):

    formulario.fields["plan_obra_social"].required = False

    formulario.fields["plan_obra_social"].empty_label = (
        "Seleccione un plan"
    )

    formulario.fields["plan_obra_social"].queryset = (
        PlanObraSocial.objects.none()
    )

    obra_social_id = None

    # Formulario enviado
    if formulario.is_bound:

        obra_social_id = formulario.data.get(
            formulario.add_prefix("obrasocial")
        )

    # Edición de paciente existente
    elif formulario.instance and formulario.instance.pk:

        obra_social_id = formulario.instance.obrasocial_id

    if obra_social_id:

        try:

            planes = PlanObraSocial.objects.filter(
                obra_social_id=obra_social_id,
                activo=True
            )

            # Mantener el plan existente aunque esté inactivo
            if (
                formulario.instance
                and formulario.instance.pk
                and formulario.instance.plan_obra_social_id
                and str(formulario.instance.obrasocial_id)
                == str(obra_social_id)
            ):

                planes = PlanObraSocial.objects.filter(
                    obra_social_id=obra_social_id
                ).filter(
                    models.Q(activo=True)
                    | models.Q(
                        pk=formulario.instance.plan_obra_social_id
                    )
                )

            formulario.fields["plan_obra_social"].queryset = (
                planes.order_by(
                    "orden",
                    "codigo",
                    "nombre"
                )
            )

        except (ValueError, TypeError):
            pass


def validar_plan_obra_social(formulario, cleaned_data):

    obra_social = cleaned_data.get("obrasocial")
    plan = cleaned_data.get("plan_obra_social")

    if plan and not obra_social:

        formulario.add_error(
            "plan_obra_social",
            "Debe seleccionar una obra social para este plan."
        )

    elif plan and obra_social:

        if plan.obra_social_id != obra_social.pk:

            formulario.add_error(
                "plan_obra_social",
                "El plan seleccionado no pertenece "
                "a la obra social indicada."
            )

    return cleaned_data


# ==========================================================
# FORMULARIO DE PACIENTE
# ==========================================================

class PacienteForm(forms.ModelForm):

    class Meta:

        model = Paciente

        fields = [
            "dni",
            "nombre",
            "apellido",
            "fecha_nacimiento",
            "telefono",
            "sexo",
            "email",
            "direccion",
            "observaciones",
            "obrasocial",
            "plan_obra_social",
            "numero_afiliado",
        ]

        widgets = {

            "dni": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "nombre": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "apellido": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "fecha_nacimiento": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),

            "sexo": forms.Select(attrs={
                "class": "form-select"
            }),

            "telefono": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control"
            }),

            "direccion": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "observaciones": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "obrasocial": forms.Select(attrs={
                "class": "form-select",
                "id": "id_obrasocial"
            }),

            "plan_obra_social": forms.Select(attrs={
                "class": "form-select",
                "id": "id_plan_obra_social"
            }),

            "numero_afiliado": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ingrese el número de afiliado"
            }),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Campos obligatorios de main
        self.fields["dni"].required = True
        self.fields["nombre"].required = True
        self.fields["apellido"].required = True

        # Campos opcionales
        self.fields["fecha_nacimiento"].required = False
        self.fields["telefono"].required = False
        self.fields["sexo"].required = False
        self.fields["email"].required = False
        self.fields["direccion"].required = False
        self.fields["observaciones"].required = False
        self.fields["obrasocial"].required = False
        self.fields["numero_afiliado"].required = False

        configurar_planes_obra_social(self)

    def clean_dni(self):

        return validar_dni_paciente(self)

    def clean(self):

        cleaned_data = super().clean()

        return validar_plan_obra_social(
            self,
            cleaned_data
        )


# ==========================================================
# BÚSQUEDA DE PACIENTES
# ==========================================================

class BusquedaPacienteForm(forms.Form):

    dni = forms.IntegerField(
        label="Ingrese el DNI"
    )


# ==========================================================
# FORMULARIO DE ACTUALIZACIÓN
# ==========================================================

class PacienteUpdateForm(forms.ModelForm):

    class Meta:

        model = Paciente

        fields = [
            "dni",
            "nombre",
            "apellido",
            "telefono",
            "sexo",
            "email",
            "direccion",
            "observaciones",
            "obrasocial",
            "plan_obra_social",
            "numero_afiliado",
        ]

        widgets = {

            "dni": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "nombre": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "apellido": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "sexo": forms.Select(attrs={
                "class": "form-select"
            }),

            "telefono": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control"
            }),

            "direccion": forms.TextInput(attrs={
                "class": "form-control"
            }),

            "observaciones": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),

            "obrasocial": forms.Select(attrs={
                "class": "form-select",
                "id": "id_obrasocial"
            }),

            "plan_obra_social": forms.Select(attrs={
                "class": "form-select",
                "id": "id_plan_obra_social"
            }),

            "numero_afiliado": forms.TextInput(attrs={
                "class": "form-control"
            }),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["dni"].required = True
        self.fields["nombre"].required = True
        self.fields["apellido"].required = True

        for campo in [
            "telefono",
            "sexo",
            "email",
            "direccion",
            "observaciones",
            "obrasocial",
            "numero_afiliado",
        ]:
            self.fields[campo].required = False

        configurar_planes_obra_social(self)

    def clean_dni(self):

        return validar_dni_paciente(self)

    def clean(self):

        cleaned_data = super().clean()

        return validar_plan_obra_social(
            self,
            cleaned_data
        )
