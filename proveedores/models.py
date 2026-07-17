from django.db import models

from django.contrib.auth.models import User

class Proveedor(models.Model):

    TIPOS = [

        ("LABORATORIO", "Laboratorio"),
        ("PATOLOGIA", "Patología"),
        ("DIAGNOSTICO", "Centro de Diagnóstico"),
        ("CARDIOLOGIA", "Cardiología"),
        ("RADIOLOGIA", "Radiología"),
        ("OTRO", "Otro"),

    ]

    nombre = models.CharField(
        max_length=150
    )

    tipo = models.CharField(
        max_length=30,
        choices=TIPOS
    )

    razon_social = models.CharField(
        max_length=200,
        blank=True
    )

    cuit = models.CharField(
        max_length=15,
        blank=True
    )

    telefono = models.CharField(
        max_length=50,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    direccion = models.CharField(
        max_length=250,
        blank=True
    )

    banco = models.CharField(
        max_length=100,
        blank=True
    )

    cbu = models.CharField(
        max_length=30,
        blank=True
    )

    alias = models.CharField(
        max_length=100,
        blank=True
    )

    activo = models.BooleanField(
        default=True
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        ordering = ["nombre"]

        verbose_name = "Proveedor"

        verbose_name_plural = "Proveedores"

    def __str__(self):

        return self.nombre
    
class LiquidacionProveedor(models.Model):

    ESTADOS = [

        ("PENDIENTE", "Pendiente"),
        ("PARCIAL", "Pago Parcial"),
        ("PAGADA", "Pagada"),
        ("ANULADA", "Anulada"),

    ]

    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.PROTECT,
        related_name="liquidaciones"
    )

    fecha = models.DateField(
        auto_now_add=True
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # NUEVOS CAMPOS
    total_pagado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    cantidad_pagos = models.PositiveIntegerField(
        default=0
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    observacion = models.TextField(
        blank=True
    )

    generado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="liquidaciones_proveedor_generadas"
    )

    fecha_generacion = models.DateTimeField(
        auto_now_add=True
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
        related_name="liquidaciones_proveedor_pagadas"
    )

    class Meta:

        ordering = [
            "-fecha_generacion"
        ]

        verbose_name = "Liquidación de Proveedor"

        verbose_name_plural = "Liquidaciones de Proveedores"

    @property
    def cantidad_prestaciones(self):
        return self.detalles.count()

    @property
    def saldo_pendiente(self):
        return self.total - self.total_pagado

    @property
    def total_calculado(self):
        from decimal import Decimal

        return (
            self.detalles.aggregate(
                total=models.Sum("importe_proveedor")
            )["total"]
            or Decimal("0.00")
        )

    def __str__(self):

        return (
            f"{self.proveedor} - {self.fecha}"
        )
        


class PagoLiquidacionProveedor(models.Model):

    liquidacion = models.ForeignKey(
        LiquidacionProveedor,
        on_delete=models.CASCADE,
        related_name="pagos"
    )

    movimiento_caja = models.ForeignKey(
    "caja.MovimientoCaja",
    on_delete=models.PROTECT,
    related_name="pagos_proveedor"
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

    class Meta:

        ordering = [
            "-fecha"
        ]

        verbose_name = "Pago de Liquidación"

        verbose_name_plural = "Pagos de Liquidaciones"

    def __str__(self):

        return (
            f"{self.liquidacion.proveedor} - ${self.importe}"
        )