from django.db import models
from especialidades.models import Especialidades
from medicos.models import Medico
from paciente.models import Paciente

class Turnos(models.Model):
    especialidad = models.ForeignKey(Especialidades, on_delete=models.CASCADE)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.fecha} {self.hora} - {self.medico} ({self.paciente})"

    class Meta:
        unique_together = ['medico', 'fecha', 'hora']  # evita duplicados de turnos

