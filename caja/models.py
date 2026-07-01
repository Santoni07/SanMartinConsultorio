from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from honorarios.models import LiquidacionMedica
from nomenclador.models import NomencladorGeneral
from core.models import CentroMedico
from paciente.models import Paciente
from turnos.models import Turnos

class CajaDiaria(models.Model):
    ESTADOS = [
        ('ABIERTA', 'Abierta'),
        ('CERRADA', 'Cerrada'),
    ]

    TURNOS = [
        ('MANANA', 'Mañana'),
        ('TARDE', 'Tarde'),
    ]

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.PROTECT,
        related_name='cajas_diarias'
    )

    fecha = models.DateField(default=timezone.localdate)

    turno = models.CharField(
        max_length=20,
        choices=TURNOS
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='ABIERTA'
    )

    abierta_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='cajas_abiertas'
    )

    cerrada_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='cajas_cerradas'
    )

    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)

    saldo_inicial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    observacion_apertura = models.TextField(blank=True, null=True)
    observacion_cierre = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Caja diaria'
        verbose_name_plural = 'Cajas diarias'
        unique_together = ('centro_medico', 'fecha', 'turno')
        ordering = ['-fecha', 'centro_medico', 'turno']

    def __str__(self):
        return (
            f'{self.centro_medico} - '
            f'{self.fecha} - '
            f'{self.get_turno_display()} - '
            f'{self.estado}'
        )

    @property
    def esta_abierta(self):
        return self.estado == 'ABIERTA'

    @property
    def total_ingresos(self):
        return self.movimientos.filter(
            tipo='INGRESO',
            estado='ACTIVO'
        ).aggregate(
            total=models.Sum('importe')
        )['total'] or 0

    @property
    def total_egresos(self):
        return self.movimientos.filter(
            tipo='EGRESO',
            estado='ACTIVO'
        ).aggregate(
            total=models.Sum('importe')
        )['total'] or 0

    @property
    def saldo_final(self):
        return self.saldo_inicial + self.total_ingresos - self.total_egresos


class MedioPago(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Medio de pago'
        verbose_name_plural = 'Medios de pago'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre



class ConceptoFacturacion(models.Model):

    nomenclador = models.OneToOneField(
    NomencladorGeneral,
    on_delete=models.PROTECT,
   
    related_name="particular"
)

    porcentaje_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    porcentaje_medico = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    porcentaje_consultorio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    activo = models.BooleanField(
        default=True
    )

    TIPOS_CALCULO = [
        ('PORCENTAJE', 'Porcentaje'),
        ('FIJO_MEDICO', 'Honorario fijo médico'),
    ]
    importe_particular = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0,
    verbose_name="Importe Particular"
)
    tipo_calculo = models.CharField(
        max_length=20,
        choices=TIPOS_CALCULO,
        default='PORCENTAJE'
    )

    honorario_fijo_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    TIPOS_CONCEPTOS = [
        ('CONSULTA', 'Consulta'),
        ('ESTUDIO', 'Estudio'),
        ('PRACTICA', 'Práctica'),
        ('CERTIFICADOS', 'Certificados'),
    ]

    tipo_concepto = models.CharField(
        max_length=20,
        choices=TIPOS_CONCEPTOS,
        default='CONSULTA'
    )

    TIPOS_PROVEEDORES = [
        ('', '---------'),
        ('PATOLOGO', 'Patólogo'),
        ('BIOQUIMICO', 'Bioquímico'),
    ]

    tipo_proveedor = models.CharField(
        max_length=20,
        choices=TIPOS_PROVEEDORES,
        blank=True,
        default=''
    )

    importe_proveedor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    class Meta:
        ordering = ['nomenclador__descripcion']
        verbose_name = "Concepto de Facturación"
        verbose_name_plural = "Conceptos de Facturación"

    def __str__(self):
        return f"{self.nomenclador.codigo} - {self.nomenclador.descripcion}"


class MovimientoCaja(models.Model):
    TIPOS = [
        ('INGRESO', 'Ingreso'),
        ('EGRESO', 'Egreso'),
    ]

    ESTADOS = [
        ('ACTIVO', 'Activo'),
        ('ANULADO', 'Anulado'),
    ]

    caja = models.ForeignKey(
        CajaDiaria,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.PROTECT,
        related_name='movimientos_caja'
    )
    concepto_facturacion = models.ForeignKey(
        ConceptoFacturacion,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    turno = models.ForeignKey(
        Turnos,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimientos_caja'
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimientos_caja'
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default='INGRESO'
    )

    medio_pago = models.ForeignKey(
        MedioPago,
        on_delete=models.PROTECT,
        related_name='movimientos'
    )

    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    concepto = models.CharField(
        max_length=200,
        default='Consulta médica'
    )

    observacion = models.TextField(blank=True, null=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default='ACTIVO'
    )

    creado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='movimientos_caja_creados'
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    anulado_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='movimientos_caja_anulados'
    )
    liquidado = models.BooleanField(
    default=False
)

    liquidacion = models.ForeignKey(
        LiquidacionMedica,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.TextField(blank=True, null=True)

    importe_bruto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    importe_iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    retencion_monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    retencion_motivo = models.CharField(
    max_length=255,
    blank=True,
    null=True
)
    importe_neto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    importe_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    importe_consultorio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
        
    
    class Meta:
        verbose_name = 'Movimiento de caja'
        verbose_name_plural = 'Movimientos de caja'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f'{self.fecha_creacion:%d/%m/%Y %H:%M} - {self.tipo} - ${self.importe}'

    def anular(self, usuario, motivo=''):
        self.estado = 'ANULADO'
        self.anulado_por = usuario
        self.fecha_anulacion = timezone.now()
        self.motivo_anulacion = motivo
        self.save()


class HistorialMovimientoCaja(models.Model):
    ACCIONES = [
        ('CREADO', 'Creado'),
        ('ANULADO', 'Anulado'),
        ('EDITADO', 'Editado'),
        ('CIERRE_CAJA', 'Cierre de caja'),
        ('APERTURA_CAJA', 'Apertura de caja'),
    ]

    caja = models.ForeignKey(
        CajaDiaria,
        on_delete=models.CASCADE,
        related_name='historial'
    )

    movimiento = models.ForeignKey(
        MovimientoCaja,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='historial'
    )

    accion = models.CharField(
        max_length=30,
        choices=ACCIONES
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='historial_caja'
    )

    centro_medico = models.ForeignKey(
        CentroMedico,
        on_delete=models.PROTECT,
        related_name='historial_caja'
    )

    fecha_hora = models.DateTimeField(auto_now_add=True)

    descripcion = models.TextField(blank=True, null=True)

    datos_anteriores = models.JSONField(blank=True, null=True)
    datos_nuevos = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = 'Historial de movimiento de caja'
        verbose_name_plural = 'Historial de movimientos de caja'
        ordering = ['-fecha_hora']

    def __str__(self):
        return f'{self.fecha_hora:%d/%m/%Y %H:%M} - {self.accion} - {self.usuario}'
    
