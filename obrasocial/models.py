from django.db import models
from nomenclador.models import NomencladorGeneral

# Create your models here.

class ObraSocial(models.Model):

    nombre = models.CharField(
        "Nombre",
        max_length=150,
        unique=True
    )

    sigla = models.CharField(
        "Sigla",
        max_length=20,
        blank=True,
        unique=True,
        null=True
    )

    codigo = models.CharField(
        "Código",
        max_length=20,
        unique=True,
        blank=True,
        
        null=True
    )

    cuit = models.CharField(
        "CUIT",
        max_length=13,
        blank=True
    )

    telefono = models.CharField(
        "Teléfono",
        max_length=50,
        blank=True
    )

    email = models.EmailField(
        "Email",
        blank=True
    )

    domicilio = models.CharField(
        "Domicilio",
        max_length=250,
        blank=True
    )

    ciudad = models.CharField(
        "Ciudad",
        max_length=100,
        blank=True
    )

    provincia = models.CharField(
        "Provincia",
        max_length=100,
        blank=True
    )

    observaciones = models.TextField(
        "Observaciones",
        blank=True
    )

    activa = models.BooleanField(
        "Activa",
        default=True
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )
    
    sitio_web = models.URLField(
    "Sitio Web",
    blank=True
    )

    portal_prestadores = models.URLField(
        "Portal de Prestadores",
        blank=True
    )

    portal_autorizaciones = models.URLField(
        "Portal de Autorizaciones",
        blank=True
    )

    portal_afiliados = models.URLField(
        "Portal de Afiliados",
        blank=True
    )

    cartilla_online = models.URLField(
        "Cartilla Médica Online",
        blank=True
    )

    credenciales_online = models.URLField(
        "Descarga de Credenciales",
        blank=True
    )

    observaciones_portal = models.TextField(
        "Observaciones del Portal",
        blank=True
    )

    class Meta:

        ordering = [
            "nombre"
        ]

        verbose_name = "Obra Social"

        verbose_name_plural = "Obras Sociales"

    def __str__(self):
        return self.nombre
    


# ==========================================================
# PLANES DE OBRAS SOCIALES
# ==========================================================

class PlanObraSocial(models.Model):

    obra_social = models.ForeignKey(
        ObraSocial,
        on_delete=models.CASCADE,
        related_name="planes",
        verbose_name="Obra Social"
    )

    codigo = models.CharField(
        "Código",
        max_length=30
    )

    nombre = models.CharField(
        "Nombre",
        max_length=150
    )

    observaciones = models.TextField(
        "Observaciones",
        blank=True
    )

    orden = models.PositiveIntegerField(
        "Orden",
        default=0
    )

    activo = models.BooleanField(
        "Activo",
        default=True
    )

    fecha_alta = models.DateTimeField(
        "Fecha de alta",
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        "Última modificación",
        auto_now=True
    )

    class Meta:

        verbose_name = "Plan"

        verbose_name_plural = "Planes"

        ordering = [
            "orden",
            "codigo",
            "nombre"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "obra_social",
                    "codigo"
                ],
                name="plan_codigo_unico_por_obra_social"
            )

        ]

    def __str__(self):

        if self.codigo:
            return f"{self.obra_social.sigla} - {self.codigo} - {self.nombre}"

        return f"{self.obra_social.sigla} - {self.nombre}"
    
# ==========================================================
# PRESTACIONES DEL PLAN
# ==========================================================

class PrestacionPlan(models.Model):

    ESTADOS = [
        ("ACTIVA", "Activa"),
        ("INACTIVA", "Inactiva"),
    ]

    plan = models.ForeignKey(
        PlanObraSocial,
        on_delete=models.CASCADE,
        related_name="prestaciones"
    )

    nomenclador = models.ForeignKey(
        NomencladorGeneral,
        on_delete=models.PROTECT,
        related_name="planes"
    )

    valor = models.DecimalField(
        "Valor Convenio",
        max_digits=12,
        decimal_places=2
    )

    fecha_vigencia_desde = models.DateField()

    fecha_vigencia_hasta = models.DateField(
        blank=True,
        null=True
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="ACTIVA"
    )

    observaciones = models.TextField(
        blank=True
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        verbose_name = "Prestación del Plan"

        verbose_name_plural = "Prestaciones del Plan"

        ordering = [
            "nomenclador__codigo"
        ]

    def __str__(self):

        return f"{self.plan} - {self.nomenclador}"

class PrestacionPlanValor(models.Model):

    prestacion = models.ForeignKey(
        PrestacionPlan,
        on_delete=models.CASCADE,
        related_name="valores"
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    vigente_desde = models.DateField()

    vigente_hasta = models.DateField(
        blank=True,
        null=True
    )

    activo = models.BooleanField(
        default=True
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )