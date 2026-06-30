from django.db import models

# Create your models here.
class NomencladorGeneral(models.Model):

    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Código"
    )

    descripcion = models.CharField(
        max_length=300,
        verbose_name="Descripción"
    )

    activo = models.BooleanField(
        default=True
    )

    observaciones = models.TextField(
        blank=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['codigo']
        verbose_name = "Nomenclador General"
        verbose_name_plural = "Nomenclador General"

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"