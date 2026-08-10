from django.db import models
from obrasocial.models import ObraSocial
from datetime import date


class Paciente(models.Model):

    SEXOS = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    nombre = models.CharField(
        max_length=50
    )

    apellido = models.CharField(
        max_length=50
    )

    dni = models.CharField(
        max_length=8,
        unique=True
    )

    fecha_nacimiento = models.DateField(
        blank=True,
        null=True
    )

    sexo = models.CharField(
        max_length=1,
        choices=SEXOS,
        blank=True,
        null=True
    )

    telefono = models.CharField(
        max_length=20,
        blank=True
    )

    email = models.EmailField(
        blank=True
    )

    direccion = models.CharField(
        max_length=100,
        blank=True
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    obrasocial = models.ForeignKey(
        ObraSocial,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    activo = models.BooleanField(
        default=True
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = date.today()

            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day)
                <
                (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )

        return None

    def save(self, *args, **kwargs):

        if self.nombre:
            self.nombre = self.nombre.strip().upper()

        if self.apellido:
            self.apellido = self.apellido.strip().upper()

        if self.email:
            self.email = self.email.strip().lower()

        if self.dni:
            self.dni = self.dni.strip()

        super().save(*args, **kwargs)