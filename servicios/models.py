from django.db import models

# Create your models here.

class Servicios(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=250)
    imagen = models.ImageField(upload_to='servicios', null=True, blank=True)

    def __str__(self):
        return self.nombre