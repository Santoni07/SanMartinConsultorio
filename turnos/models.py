from django.db import models
from especialidades.models import Especialidades
from medicos.models import Medico
from paciente.models import Paciente
from core.models import CentroMedico
from django.contrib.auth.models import User

class Consultorio(models.Model):

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.CASCADE
    )

    numero = models.IntegerField()

    class Meta:
        unique_together = ('centro_medico', 'numero')

    def __str__(self):
        return f"{self.centro_medico} - Consultorio {self.numero}"
    
class Turnos(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ATENDIDO', 'Atendido'),
        ('AUSENTE', 'Ausente'),
        ('CANCELADO', 'Cancelado'),
    ]

    # 🔵 SEDE A LA QUE PERTENECE EL TURNO
    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos'
    )

    # 🔵 DESDE QUÉ SEDE SE OPERÓ
    sede_operacion = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_operados'
    )

    especialidad = models.ForeignKey(
        Especialidades,
        on_delete=models.CASCADE
    )

    medico = models.ForeignKey(
        Medico,
        on_delete=models.CASCADE
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE
    )

    fecha = models.DateField()

    hora = models.TimeField()

    observaciones = models.TextField(
        blank=True
    )

    es_sobreturno = models.BooleanField(
        default=False
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default='PENDIENTE'
    )

    # =====================================================
    # 🔥 TRAZABILIDAD
    # =====================================================

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_creados'
    )

    modificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_modificados'
    )

    cancelado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turnos_cancelados'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True
    )

    fecha_cancelacion = models.DateTimeField(
        null=True,
        blank=True
    )

    # =====================================================

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

    medico = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE
    )

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    dia_semana = models.IntegerField(
        choices=DIAS
    )

    hora_inicio = models.TimeField()

    hora_fin = models.TimeField()

    duracion_turno = models.IntegerField(
        default=20
    )

    def __str__(self):
        return f"{self.medico} - {self.get_dia_semana_display()}"


class AgendaMedico(models.Model):

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendas'
    )

    medico = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE
    )

    consultorio = models.ForeignKey(
        Consultorio,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    fecha = models.DateField()

    hora_inicio = models.TimeField()

    hora_fin = models.TimeField()

    duracion_turno = models.IntegerField(
        default=20
    )

    # =========================================
    # 🔥 TRAZABILIDAD
    # =========================================

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendas_creadas'
    )

    modificado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendas_modificadas'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True
    )

    sede_operacion = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendas_operadas'
    )

    # =========================================

    def __str__(self):

        return f"{self.medico} - {self.fecha}"
    
class ExcepcionAgenda(models.Model):

    TIPO = [
        ('CERRADO', 'No atiende'),
        ('MODIFICADO', 'Modificar horario'),
        ('REPROGRAMAR', 'Cambiar de día'),
    ]

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='excepciones'
    )

    medico = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE
    )

    fecha = models.DateField()

    tipo = models.CharField(
        max_length=20,
        choices=TIPO
    )

    hora_inicio = models.TimeField(
        null=True,
        blank=True
    )

    hora_fin = models.TimeField(
        null=True,
        blank=True
    )

    nueva_fecha = models.DateField(
        null=True,
        blank=True
    )

    motivo = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # =========================================
    # 🔥 TRAZABILIDAD
    # =========================================

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='excepciones_creadas'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    sede_operacion = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='excepciones_operadas'
    )

    # =========================================

    def __str__(self):

        return f"{self.medico} - {self.fecha} - {self.tipo}"
    
class Sobreturno(models.Model):

    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('ATENDIDO', 'Atendido'),
        ('AUSENTE', 'Ausente'),
        ('CANCELADO', 'Cancelado'),
    ]

    medico = models.ForeignKey(
        'medicos.Medico',
        on_delete=models.CASCADE
    )

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sobreturnos'
    )

    sede_operacion = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sobreturnos_operados'
    )

    paciente = models.ForeignKey(
        'paciente.Paciente',
        on_delete=models.CASCADE
    )

    fecha = models.DateField()

    hora = models.TimeField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='PENDIENTE'
    )

    observaciones = models.TextField(
        blank=True,
        null=True
    )

    # =========================================
    # 🔥 TRAZABILIDAD
    # =========================================

    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sobreturnos_creados'
    )

    cancelado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sobreturnos_cancelados'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_cancelacion = models.DateTimeField(
        null=True,
        blank=True
    )

    # =========================================

    creado = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return f"Sobreturno - {self.medico} - {self.fecha} {self.hora}" 
    
class HistorialTurno(models.Model):

    ACCIONES = [
        ('CREADO', 'Creado'),
        ('MODIFICADO', 'Modificado'),
        ('CANCELADO', 'Cancelado'),
        ('REPROGRAMADO', 'Reprogramado'),
        ('AUSENTE', 'Ausente'),
        ('EXCEPCION', 'Excepción'),
    ]

    turno = models.ForeignKey(
        Turnos,
        on_delete=models.CASCADE,
        related_name='historial'
    )

    accion = models.CharField(
        max_length=20,
        choices=ACCIONES
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    sede_operacion = models.ForeignKey(
        CentroMedico,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fecha = models.DateTimeField(
        auto_now_add=True
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    datos_anteriores = models.JSONField(
        null=True,
        blank=True
    )

    datos_nuevos = models.JSONField(
        null=True,
        blank=True
    )

    def __str__(self):

        return f"{self.turno} - {self.accion}"