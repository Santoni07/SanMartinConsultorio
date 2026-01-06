from django.db import models
from obrasocial.models import ObraSocial

# Create your models here.

class Paciente(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    edad = models.IntegerField(default=0, blank=False, null=False)
    dni = models.CharField(max_length=8)
    fecha_nacimiento = models.DateField( auto_now=False, auto_now_add=False)
    telefono = models.IntegerField( )
    email = models.EmailField()
    direccion = models.CharField(max_length=100)
    observaciones = models.TextField()
    obrasocial=models.ForeignKey(ObraSocial, on_delete=models.CASCADE)
   
    
    

        
    def __str__(self):
        return f"{self.apellido}, {self.nombre}"