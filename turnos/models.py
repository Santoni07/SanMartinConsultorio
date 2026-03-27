from django.db import models
from especialidades.models import Especialidades
from medicos.models import Medico
from paciente.models import Paciente

class Turnos(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ATENDIDO', 'Atendido'),
        ('AUSENTE', 'Ausente'),
    ]

    especialidad = models.ForeignKey(Especialidades, on_delete=models.CASCADE)
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    observaciones = models.TextField(blank=True)
    es_sobreturno = models.BooleanField(default=False)
    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='PENDIENTE'
    )

    def __str__(self):
        return f"{self.fecha} {self.hora} - {self.medico} ({self.paciente})"

   
        
        
class DisponibilidadMedico(models.Model):

    DIAS = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
    ]

    medico = models.ForeignKey('medicos.Medico', on_delete=models.CASCADE)
    dia_semana = models.IntegerField(choices=DIAS)

    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    duracion_turno = models.IntegerField(default=20)

    def __str__(self):
        return f"{self.medico} - {self.get_dia_semana_display()}"
    
class AgendaMedico(models.Model):

    medico = models.ForeignKey('medicos.Medico', on_delete=models.CASCADE)
    fecha = models.DateField()

    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()

    duracion_turno = models.IntegerField(default=20)

    def __str__(self):
        return f"{self.medico} - {self.fecha}"