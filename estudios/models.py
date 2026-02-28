from django.db import models
from paciente.models import Paciente
from historial.models import ConsultaMedica

TIPOS_ESTUDIO = [
    ('ecografia', 'Ecografía'),
    ('electrocardiograma', 'Electrocardiograma'),
    ('laboratorio', 'Laboratorio'),
    ('resonancia', 'Resonancia Magnética'),
    ('tomografia', 'Tomografía'),
    ('telemetria', 'Telemetría'),
    ('ecocardiograma', 'Ecocardiograma'),
    ('otros', 'Otros'),
]

class Estudio(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='estudios')
    tipo = models.CharField(max_length=30, choices=TIPOS_ESTUDIO)
    fecha = models.DateField()
    descripcion = models.TextField(blank=True, null=True)
    archivo = models.FileField(upload_to='estudios/', blank=True, null=True)
    consulta = models.ForeignKey(
    ConsultaMedica,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='estudios'
)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.paciente} ({self.fecha})"
