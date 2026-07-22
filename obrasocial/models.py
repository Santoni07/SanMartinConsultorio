from django.db import models

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
    

class PlanObraSocial(models.Model):

    obra_social = models.ForeignKey(

        ObraSocial,

        on_delete=models.PROTECT,

        related_name="planes",

        verbose_name="Obra Social"

    )

    nombre = models.CharField(

        "Nombre",

        max_length=150

    )

    codigo = models.CharField(

        "Código",

        max_length=30,

        blank=True

    )

    descripcion = models.TextField(

        "Descripción",

        blank=True

    )

    activo = models.BooleanField(

        default=True

    )

    fecha_alta = models.DateTimeField(

        auto_now_add=True

    )

    class Meta:

        ordering = [

            "obra_social",

            "nombre"

        ]

        verbose_name = "Plan"

        verbose_name_plural = "Planes"

        constraints = [

            models.UniqueConstraint(

                fields=[

                    "obra_social",

                    "nombre"

                ],

                name="plan_unico_por_obra_social"

            )

        ]

    def __str__(self):

        return f"{self.obra_social} - {self.nombre}"