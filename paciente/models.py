from django.db import models
from obrasocial.models import ObraSocial
from datetime import date


class Paciente(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.CharField(max_length=8, unique=True)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    direccion = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, null=True)
    obrasocial = models.ForeignKey(ObraSocial, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None