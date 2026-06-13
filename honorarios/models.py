from django.db import models
from django.contrib.auth.models import User

from medicos.models import Medico
from core.models import CentroMedico


class LiquidacionMedica(models.Model):

    medico = models.ForeignKey(
        Medico,
        on_delete=models.PROTECT,
        related_name='liquidaciones'
    )

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.PROTECT,
        related_name='liquidaciones_medicas'
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    cantidad_prestaciones = models.IntegerField(
        default=0
    )

    total_bruto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_retenciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_consultorio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_honorarios = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    observacion = models.TextField(
        blank=True,
        null=True
    )

    generado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='liquidaciones_generadas'
    )
    ESTADOS = [
    ('PENDIENTE', 'Pendiente de pago'),
    ('PARCIAL', 'Pago parcial'),
    ('PAGADA', 'Pagada'),
    ]

    estado = models.CharField(
    max_length=20,
    choices=ESTADOS,
    default='PENDIENTE'
    )
    total_pagado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    fecha_pago = models.DateTimeField(
    null=True,
    blank=True
    )

    pagado_por = models.ForeignKey(
    User,
    on_delete=models.PROTECT,
    null=True,
    blank=True,
    related_name='liquidaciones_pagadas'
    )
    cantidad_pagos = models.IntegerField(
        default=0
    )
    
    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return (
            f'{self.medico} - '
            f'{self.fecha:%d/%m/%Y} - '
            f'${self.total_honorarios}'
        )
    @property
    def saldo_pendiente(self):

        return (
            self.total_honorarios -
            self.total_pagado
        )
        
class PagoLiquidacionMedica(models.Model):

    liquidacion = models.ForeignKey(
        LiquidacionMedica,
        on_delete=models.CASCADE,
        related_name='pagos'
    )

    movimiento_caja = models.ForeignKey(
        'caja.MovimientoCaja',
        on_delete=models.PROTECT
    )

    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    registrado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )