from django import forms
from .models import CajaDiaria, MovimientoCaja, MedioPago,ConceptoFacturacion
from django.utils import timezone
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

class MovimientoCajaForm(forms.ModelForm):

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
        ]

        widgets = {
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),

            'concepto_facturacion': forms.Select(attrs={
                'class': 'form-select'
            }),

           

            'importe': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
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

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.fields['retencion_monto'].required = False
        self.fields['retencion_motivo'].required = False

       

        self.fields[
            'concepto_facturacion'
        ].queryset = ConceptoFacturacion.objects.filter(
            activo=True
        ).order_by('nombre')





class CobroConsultaForm(forms.ModelForm):

    turno = forms.ModelChoiceField(
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

        

        # ===========================
        # PRESTACIONES
        # ===========================

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

        # El importe se mostrará por AJAX
        self.fields['importe_particular'].initial = 0

        # ===========================
        # TURNOS
        # ===========================

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
                    'medico',
                    'especialidad'
                )
                .order_by('hora')
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
            "tipo_proveedor",
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

            "tipo_proveedor": forms.Select(attrs={
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
            "tipo_proveedor": "Proveedor",
            "importe_proveedor": "Importe proveedor",
        }