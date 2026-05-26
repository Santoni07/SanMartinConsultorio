from django.db import models

class CentroMedico(models.Model):

    nombre = models.CharField(max_length=200)

    direccion = models.CharField(max_length=300)

    telefono = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    email = models.EmailField(
        blank=True,
        null=True
    )

    activo = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Centro Médico"
        verbose_name_plural = "Centros Médicos"

    def __str__(self):
        return self.nombre 
