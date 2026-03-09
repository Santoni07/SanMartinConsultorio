from django.db import models

from django.db import models
from paciente.models import Paciente
from medicos.models import Medico
from turnos.models import Turnos

class HistoriaClinica(models.Model):
    paciente = models.OneToOneField(Paciente, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    observaciones_generales = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Historia Clínica de {self.paciente}"

class ConsultaMedica(models.Model):
    historia_clinica = models.ForeignKey(HistoriaClinica, on_delete=models.CASCADE, related_name='consultas')
    medico = models.ForeignKey(Medico, on_delete=models.SET_NULL, null=True)
    fecha = models.DateField()
    motivo = models.CharField(max_length=255)
    examen_fisico = models.TextField(blank=True, null=True) 
    diagnostico = models.TextField()
    tratamiento = models.TextField()
    observaciones = models.TextField(blank=True, null=True)
    turno = models.OneToOneField(
    Turnos,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='consulta'
)

    def __str__(self):
        return f"Consulta de {self.historia_clinica.paciente} el {self.fecha}"