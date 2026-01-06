from django.db import models


# Create your models here.
class Especialidades(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion =models.TextField()
    img = models.ImageField(upload_to='especialidad', null=True, blank=True)

    def __str__(self):
        return self.nombre
