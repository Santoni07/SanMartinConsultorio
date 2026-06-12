from django.db import models
from medicos.models import Medico
from core.models import CentroMedico
from django.contrib.auth.models import User

# Create your models here.
class LiquidacionMedica(models.Model):

    medico = models.ForeignKey(
        Medico,
        on_delete=models.PROTECT
    )

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.PROTECT
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    total_honorarios = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    total_consultorio = models.DecimalField(
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

    cantidad_prestaciones = models.IntegerField(
        default=0
    )

    generado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT
    )
    observacion = models.TextField(
    blank=True,
    null=True
)