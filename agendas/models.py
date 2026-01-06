# Create your models here.

from datetime import date

from django.forms import ValidationError

from django.db import models

from paciente.models import Paciente
from medicos.models import Medico
def validar_dia(value):
    hoy = date.today()
    nombres_dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    fecha_iso = str(value)  # Convertir a cadena si no lo es
    dia_semana = nombres_dias[date.fromisoformat(fecha_iso).weekday()]      
   
    if value < hoy:
        raise ValidationError('No es posible elegir una fecha tardía.')
    if (dia_semana == 'sábado') or (dia_semana == 'domingo'):
        raise ValidationError('Elija un día laborable de la semana.')

class Agendas(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='agenda')
    dia = models.DateField(help_text="Introduzca una fecha para el calendario")
    
    
    HORARIOS = (
        ("1", "07:00 hasta 07:30"),
        ("2", "07:30 hasta 08:00"),
        ("3", "08:00 hasta 08:30"),
        ("4", "08:30 hasta 09:00"),
        ("5", "09:00 hasta 09:30"),
        ("6", "09:30 hasta 10:00"),
        ("7", "10:00 hasta 10:30"),
        ("8", "10:30 hasta 11:00"),
        ("9", "11:00 hasta 11:30"),
        ("10", "11:30 hasta 12:00"),
        ("11", "12:00 hasta 12:30"),
        ("12", "12:30 hasta 13:00"),
        ("13", "13:00 hasta 13:30"),
        ("14", "13:30 hasta 14:00"),
        ("15", "14:00 hasta 14:30"),
        ("16", "14:30 hasta 15:00"),
        ("17", "15:00 hasta 15:30"),
        ("18", "15:30 hasta 16:00"),
        ("19", "16:00 hasta 16:30"),
        ("20", "16:30 hasta 17:00"),
        ("21", "17:00 hasta 17:30"),
        ("22", "17:30 hasta 18:00"),
        ("23", "18:00 hasta 18:30"),
        ("24", "18:30 hasta 19:00"),
        ("25", "19:00 hasta 19:30"),
        ("26", "19:30 hasta 20:00"),
        ("27", "20:00 hasta 20:30"),
        ("28", "20:30 hasta 21:00"),
    )
    
    horario = models.CharField(max_length=10, choices=HORARIOS)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, blank=True, null=True)
    atendido = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('horario', 'dia')
        
    def __str__(self):
        return f'{self.dia.day} - {self.get_horario_display()} - {self.medico}'