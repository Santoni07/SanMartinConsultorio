
from django import forms
from django.utils import timezone

from .models import (
    CajaDiaria,
    MovimientoCaja,
    MedioPago,
    ConceptoFacturacion,
    DetalleMovimientoCaja,
    ExtraCoseguro,
)
from turnos.models import Turnos


class AperturaCajaForm(forms.ModelForm):
    class Meta:
        model = CajaDiaria
        fields = [
            'turno',
            'saldo_inicial',
            'observacion_apertura',
        ]

        widgets = {
            'turno': forms.Select(attrs={
                'class': 'form-select'
            }),
            'saldo_inicial': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ingrese saldo inicial'
            }),
            'observacion_apertura': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones de apertura'
            }),
        }


class DetalleExtraIngresoChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):

        turno = obj.movimiento.turno
        paciente = turno.paciente
        medico = turno.medico
        obra_social = paciente.obrasocial

        indicador = (
            "SOBRETURNO — "
            if turno.es_sobreturno
            else ""
        )

        return (
            f"{indicador}"
            f"{paciente.apellido.upper()}, {paciente.nombre} — "
            f"{turno.hora.strftime('%H:%M')} — "
            f"Dr. {medico.nombre} {medico.apellido} — "
            f"{obra_social.nombre}"
        )


class ExtraCoseguroEgresoChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):

        turno = obj.turno
        paciente = obj.paciente
        medico = obj.medico
        obra_social = paciente.obrasocial

        indicador = (
            "SOBRETURNO — "
            if turno.es_sobreturno
            else ""
        )

        return (
            f"{indicador}"
            f"{paciente.apellido.upper()}, {paciente.nombre} — "
            f"{turno.hora.strftime('%H:%M')} — "
            f"Dr. {medico.nombre} {medico.apellido} — "
            f"{obra_social.nombre}"
        )


class MovimientoCajaForm(forms.ModelForm):

    detalle_extra_ingreso = DetalleExtraIngresoChoiceField(
        queryset=DetalleMovimientoCaja.objects.none(),
        required=False,
        label="Paciente / turno relacionado",
        empty_label="Seleccione el turno"
    )

    extra_coseguro_egreso = ExtraCoseguroEgresoChoiceField(
        queryset=ExtraCoseguro.objects.none(),
        required=False,
        label="Paciente / turno relacionado",
        empty_label="Seleccione el extra entregado al médico"
    )

    class Meta:
        model = MovimientoCaja

        fields = [
            'tipo',
            'concepto_facturacion',
            'importe',
            'retencion_monto',
            'retencion_motivo',
            'concepto',
            'observacion',
            'tipo_egreso_depilacion',
        ]

        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),

            'concepto_facturacion': forms.Select(attrs={
                'class': 'form-select'
            }),

            'tipo_egreso_depilacion': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            }),

            'importe': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),

            'retencion_monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),

            'retencion_motivo': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'concepto': forms.TextInput(attrs={
                'class': 'form-control'
            }),

            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }

    def __init__(
        self,
        *args,
        centro_medico=None,
        fecha=None,
        **kwargs
    ):

        super().__init__(*args, **kwargs)

        self.fields['retencion_monto'].required = False
        self.fields['retencion_motivo'].required = False

        # Mantener funcionalidad de depilación de main.
        self.fields['tipo_egreso_depilacion'].required = False
        self.fields['tipo_egreso_depilacion'].choices = (
            MovimientoCaja.TIPOS_EGRESO_DEPILACION
        )

        conceptos = (
            ConceptoFacturacion.objects
            .filter(activo=True)
            .select_related("nomenclador")
            .order_by("nomenclador__descripcion")
        )

        self.fields[
            'concepto_facturacion'
        ].queryset = conceptos

        concepto_extra = conceptos.filter(
            nomenclador__codigo__iexact="EXTRA_COSEGURO"
        ).first()

        self.fields[
            'concepto_facturacion'
        ].widget.attrs["data-extra-concepto-id"] = (
            concepto_extra.id
            if concepto_extra
            else ""
        )

        if not centro_medico or not fecha:
            return

        # Prestaciones originales disponibles
        # para registrar un ingreso extra.

        self.fields[
            "detalle_extra_ingreso"
        ].queryset = (
            DetalleMovimientoCaja.objects
            .filter(
                movimiento__centro_medico=centro_medico,
                movimiento__estado="ACTIVO",
                movimiento__turno__isnull=False,
                movimiento__turno__fecha=fecha,
                movimiento__turno__estado__in=[
                    "PENDIENTE",
                    "ATENDIDO",
                ],
                prestacion_obra_social__isnull=False,
            )
            .exclude(
                estado="ANULADO"
            )
            .exclude(
                extra_coseguro__isnull=False
            )
            .select_related(
                "movimiento__turno",
                "movimiento__turno__paciente",
                "movimiento__turno__paciente__obrasocial",
                "movimiento__turno__medico",
            )
            .order_by(
                "movimiento__turno__hora",
                "id",
            )
        )

        # Extras ingresados que todavía
        # no tienen egreso.

        self.fields[
            "extra_coseguro_egreso"
        ].queryset = (
            ExtraCoseguro.objects
            .filter(
                centro_medico=centro_medico,
                fecha=fecha,
                ingreso_movimiento__estado="ACTIVO",
                egreso_movimiento__isnull=True,
            )
            .select_related(
                "turno",
                "paciente",
                "paciente__obrasocial",
                "medico",
            )
            .order_by(
                "turno__hora",
                "id",
            )
        )

    def clean(self):

        cleaned_data = super().clean()

        tipo = cleaned_data.get("tipo")
        concepto = cleaned_data.get("concepto_facturacion")
        importe = cleaned_data.get("importe")

        detalle_ingreso = cleaned_data.get(
            "detalle_extra_ingreso"
        )

        extra_egreso = cleaned_data.get(
            "extra_coseguro_egreso"
        )

        codigo = ""

        if concepto and concepto.nomenclador:
            codigo = concepto.nomenclador.codigo.upper().strip()

        es_extra = codigo == "EXTRA_COSEGURO"

        # Validar ingreso de extra de coseguro.
        if es_extra and tipo == "INGRESO":

            if not detalle_ingreso:
                self.add_error(
                    "detalle_extra_ingreso",
                    "Debe seleccionar el paciente y turno."
                )

        # Validar egreso de extra de coseguro.
        if es_extra and tipo == "EGRESO":

            if not extra_egreso:
                self.add_error(
                    "extra_coseguro_egreso",
                    "Debe seleccionar el ingreso extra correspondiente."
                )

            elif importe != extra_egreso.importe_extra:
                self.add_error(
                    "importe",
                    (
                        "El egreso debe coincidir con el importe "
                        f"entregado al médico: "
                        f"${extra_egreso.importe_extra}."
                    )
                )

        # Mantener comportamiento de depilación.
        tipo_egreso = cleaned_data.get(
            "tipo_egreso_depilacion"
        )

        if tipo != "EGRESO":
            cleaned_data["tipo_egreso_depilacion"] = None
            cleaned_data["es_depilacion"] = False
        else:
            cleaned_data["es_depilacion"] = bool(tipo_egreso)

        if not es_extra:
            cleaned_data["detalle_extra_ingreso"] = None
            cleaned_data["extra_coseguro_egreso"] = None

        return cleaned_data


class TurnoChoiceField(forms.ModelChoiceField):

    def label_from_instance(self, obj):

        if obj.es_sobreturno:
            return (
                f"SOBRETURNO | "
                f"{obj.fecha.strftime('%d/%m/%Y')} "
                f"{obj.hora.strftime('%H:%M')} - "
                f"{obj.medico} ({obj.paciente})"
            )

        return (
            f"{obj.fecha.strftime('%d/%m/%Y')} "
            f"{obj.hora.strftime('%H:%M')} - "
            f"{obj.medico} ({obj.paciente})"
        )


class CobroConsultaForm(forms.ModelForm):

    turno = TurnoChoiceField(
        queryset=Turnos.objects.none(),
        required=True,
        label='Turno a cobrar',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )

    importe_particular = forms.DecimalField(
        label='Importe',
        required=False,
        decimal_places=2,
        max_digits=12,
        disabled=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = MovimientoCaja

        fields = [
            'turno',
            'concepto_facturacion',
            'retencion_monto',
            'retencion_motivo',
            'observacion',
        ]

        widgets = {
            'concepto_facturacion': forms.Select(attrs={
                'class': 'form-select'
            }),

            'retencion_monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Retención opcional'
            }),

            'retencion_motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Motivo de la retención'
            }),

            'observacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observación opcional'
            }),
        }

    def __init__(self, *args, **kwargs):

        centro_medico = kwargs.pop(
            'centro_medico',
            None
        )

        super().__init__(*args, **kwargs)

        # Prestaciones.
        self.fields['concepto_facturacion'].queryset = (
            ConceptoFacturacion.objects.filter(
                activo=True
            )
            .select_related('nomenclador')
            .order_by('nomenclador__descripcion')
        )

        self.fields['concepto_facturacion'].empty_label = (
            "Seleccione una prestación"
        )

        self.fields['importe_particular'].initial = 0

        # Turnos.
        if centro_medico:

            turnos_cobrados = MovimientoCaja.objects.filter(
                turno__isnull=False,
                tipo='INGRESO',
                estado='ACTIVO'
            ).values_list(
                'turno_id',
                flat=True
            )

            self.fields['turno'].queryset = (
                Turnos.objects.filter(
                    centro_medico=centro_medico,
                    fecha=timezone.localdate(),
                    estado__in=[
                        'PENDIENTE',
                        'ATENDIDO'
                    ]
                )
                .exclude(
                    id__in=turnos_cobrados
                )
                .select_related(
                    'paciente',
                    'medico'
                )
                .order_by(
                    'hora',
                    'es_sobreturno'
                )
            )


class AnularMovimientoCajaForm(forms.Form):

    motivo_anulacion = forms.CharField(
        label='Motivo de anulación',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explique el motivo de la anulación'
        }),
        required=True
    )


class CerrarCajaForm(forms.ModelForm):

    class Meta:
        model = CajaDiaria
        fields = [
            'observacion_cierre',
        ]

        widgets = {
            'observacion_cierre': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones del cierre de caja'
            }),
        }


class ConceptoFacturacionForm(forms.ModelForm):

    class Meta:
        model = ConceptoFacturacion

        fields = [
            "nomenclador",
            "importe_particular",
            "porcentaje_iva",
            "tipo_calculo",
            "porcentaje_medico",
            "porcentaje_consultorio",
            "honorario_fijo_medico",
            "tipo_concepto",
            "proveedor",
            "importe_proveedor",
            "activo",
        ]

        widgets = {
            "nomenclador": forms.Select(attrs={
                'class': 'form-select select2'
            }),

            "importe_particular": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "porcentaje_iva": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "tipo_calculo": forms.Select(attrs={
                "class": "form-select"
            }),

            "porcentaje_medico": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "porcentaje_consultorio": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "honorario_fijo_medico": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "tipo_concepto": forms.Select(attrs={
                "class": "form-select"
            }),

            "proveedor": forms.Select(attrs={
                "class": "form-select"
            }),

            "importe_proveedor": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "activo": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }

        labels = {
            "nomenclador": "Prestación",
            "importe_particular": "Importe Particular",
            "porcentaje_iva": "IVA (%)",
            "porcentaje_medico": "Porcentaje Médico",
            "porcentaje_consultorio": "Porcentaje Consultorio",
            "honorario_fijo_medico": "Honorario fijo",
            "tipo_concepto": "Tipo de prestación",
            "proveedor": "Proveedor",
            "importe_proveedor": "Importe proveedor",
        }
