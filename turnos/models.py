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

class ExcepcionAgenda(models.Model):

    TIPO = [
        ('CERRADO', 'No atiende'),
        ('MODIFICADO', 'Modificar horario'),
        ('REPROGRAMAR', 'Cambiar de día'),
    ]

    medico = models.ForeignKey('medicos.Medico', on_delete=models.CASCADE)
    fecha = models.DateField()

    tipo = models.CharField(max_length=20, choices=TIPO)

    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)

    nueva_fecha = models.DateField(null=True, blank=True)  # 🔥 NUEVO

    motivo = models.CharField(max_length=255, blank=True, null=True)
    
class Sobreturno(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ATENDIDO', 'Atendido'),
        ('CANCELADO', 'Cancelado'),
    ]

    medico = models.ForeignKey('medicos.Medico', on_delete=models.CASCADE)
    paciente = models.ForeignKey('paciente.Paciente', on_delete=models.CASCADE)

    fecha = models.DateField()
    hora = models.TimeField()

    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')

    observaciones = models.TextField(blank=True, null=True)

    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sobreturno - {self.medico} - {self.fecha} {self.hora}"