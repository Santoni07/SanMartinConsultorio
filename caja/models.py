from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from honorarios.models import LiquidacionMedica
from nomenclador.models import NomencladorGeneral
from core.models import CentroMedico
from paciente.models import Paciente
from turnos.models import Turnos
from medicos.models import Medico
from decimal import Decimal

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
    blank=True,
    null=True,
   
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

        return (
            f"{self.nomenclador.codigo} - {self.nomenclador.descripcion}"
            if self.nomenclador
            else f"Concepto #{self.id} (Sin nomenclador)"
        )  

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

    def anular(self, usuario, motivo=""):

        self.estado = "ANULADO"

        self.anulado_por = usuario

        self.fecha_anulacion = timezone.now()

        self.motivo_anulacion = motivo

        self.save()

        self.detalles.update(
            estado="ANULADO"
        )

        if self.turno:

            self.turno.estado = "PENDIENTE"

            self.turno.save(
                update_fields=["estado"]
            )
        
    def recalcular_totales(self):
        """
        Recalcula todos los importes del movimiento a partir de sus detalles.
        """

        detalles = self.detalles.exclude(estado="ANULADO")

        self.importe_bruto = sum(
            (detalle.importe for detalle in detalles),
            Decimal("0.00")
        )

        self.importe_iva = sum(
            (detalle.importe_iva for detalle in detalles),
            Decimal("0.00")
        )

        self.importe_neto = sum(
            (detalle.importe_neto for detalle in detalles),
            Decimal("0.00")
        )

        self.importe_medico = sum(
            (detalle.importe_medico for detalle in detalles),
            Decimal("0.00")
        )

        self.importe_consultorio = sum(
            (detalle.importe_consultorio for detalle in detalles),
            Decimal("0.00")
        )

        # El importe total del movimiento será el bruto
        self.importe = self.importe_bruto

        self.save(
            update_fields=[
                "importe",
                "importe_bruto",
                "importe_iva",
                "importe_neto",
                "importe_medico",
                "importe_consultorio",
            ]
        )
        
    


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


class DetalleMovimientoCaja(models.Model):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("LIQUIDADO", "Liquidado"),
        ("ANULADO", "Anulado"),
    ]

    movimiento = models.ForeignKey(
        MovimientoCaja,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Movimiento de Caja"
    )

    concepto_facturacion = models.ForeignKey(
        ConceptoFacturacion,
        on_delete=models.PROTECT,
        verbose_name="Prestación"
    )

    # ==========================================
    # FOTOGRAFÍA DEL NOMENCLADOR
    # ==========================================

    codigo = models.CharField(
        max_length=20,
        verbose_name="Código"
    )

    descripcion = models.CharField(
        max_length=250,
        verbose_name="Descripción"
    )

    tipo_concepto = models.CharField(
        max_length=20,
        choices=ConceptoFacturacion.TIPOS_CONCEPTOS,
        verbose_name="Tipo de prestación"
    )

    # ==========================================
    # DATOS DE LA PRESTACIÓN
    # ==========================================

    fecha_prestacion = models.DateField(
        verbose_name="Fecha de la prestación"
    )

    cantidad = models.PositiveIntegerField(
        default=1,
        verbose_name="Cantidad"
    )

    # ==========================================
    # CONFIGURACIÓN UTILIZADA
    # (Fotografía para auditoría)
    # ==========================================

    tipo_calculo = models.CharField(
        max_length=20,
        choices=ConceptoFacturacion.TIPOS_CALCULO,
        verbose_name="Tipo de cálculo"
    )

    porcentaje_iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="IVA (%)"
    )

    porcentaje_medico = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Honorario Médico (%)"
    )

    porcentaje_consultorio = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Consultorio (%)"
    )

    honorario_fijo_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Honorario fijo"
    )

    tipo_proveedor = models.CharField(
        max_length=20,
        choices=ConceptoFacturacion.TIPOS_PROVEEDORES,
        blank=True,
        default="",
        verbose_name="Proveedor"
    )

    importe_proveedor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Importe proveedor"
    )

    # ==========================================
    # IMPORTES CALCULADOS
    # ==========================================

    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Importe Bruto"
    )

    importe_iva = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="IVA"
    )

    importe_neto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Importe Neto"
    )

    importe_medico = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Honorario Médico"
    )

    importe_consultorio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Importe Consultorio"
    )

    # ==========================================
    # ESTADO
    # ==========================================

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE",
        verbose_name="Estado"
    )

    orden = models.PositiveIntegerField(
        default=1,
        verbose_name="Orden"
    )

    observacion = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Observación"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )
    liquidacion = models.ForeignKey(
        "honorarios.LiquidacionMedica",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="detalles",
        verbose_name="Liquidación"
    )
    class Meta:

        verbose_name = "Detalle de Movimiento"

        verbose_name_plural = "Detalles de Movimiento"

        ordering = [
            "orden",
            "id"
        ]
        
    def copiar_desde_concepto(self, concepto):
        """
        Copia la configuración completa del ConceptoFacturacion.
        De esta forma el detalle conserva una fotografía histórica,
        aunque el concepto cambie en el futuro.
        """

        self.concepto_facturacion = concepto

        # ===============================
        # Datos del nomenclador
        # ===============================

        self.codigo = concepto.nomenclador.codigo
        self.descripcion = concepto.nomenclador.descripcion
        self.tipo_concepto = concepto.tipo_concepto

        # ===============================
        # Configuración de cálculo
        # ===============================

        self.tipo_calculo = concepto.tipo_calculo

        self.porcentaje_iva = concepto.porcentaje_iva

        self.porcentaje_medico = concepto.porcentaje_medico

        self.porcentaje_consultorio = concepto.porcentaje_consultorio

        self.honorario_fijo_medico = concepto.honorario_fijo_medico

        # ===============================
        # Proveedor
        # ===============================

        self.tipo_proveedor = concepto.tipo_proveedor

        self.importe_proveedor = concepto.importe_proveedor

        # ===============================
        # Importe Particular
        # ===============================

        self.importe = (
            Decimal(self.cantidad) *
            concepto.importe_particular
        )
            
    
    
    def calcular_importes(self):
        """
        Calcula todos los importes del detalle de la prestación.
        Este método trabaja únicamente con la fotografía almacenada
        en el detalle, sin volver a consultar ConceptoFacturacion.
        """

        # ==========================================
        # IMPORTE BRUTO
        # ==========================================

        self.importe = Decimal(self.importe)

        # ==========================================
        # IVA
        # ==========================================

        self.importe_iva = (
            self.importe *
            self.porcentaje_iva
        ) / Decimal("100")

        # ==========================================
        # IMPORTE NETO
        # ==========================================

        self.importe_neto = (
            self.importe -
            self.importe_iva
        )

        # ==========================================
        # HONORARIOS
        # ==========================================

        if self.tipo_calculo == "PORCENTAJE":

            self.importe_medico = (
                self.importe_neto *
                self.porcentaje_medico
            ) / Decimal("100")

            self.importe_consultorio = (
                self.importe_neto *
                self.porcentaje_consultorio
            ) / Decimal("100")

        elif self.tipo_calculo == "FIJO_MEDICO":

            self.importe_medico = self.honorario_fijo_medico

            self.importe_consultorio = (
                self.importe_neto -
                self.importe_medico
            )

        else:

            self.importe_medico = Decimal("0.00")
            self.importe_consultorio = self.importe_neto
    
    def save(self, *args, **kwargs):
        """
        Antes de guardar:
        - Copia la configuración del ConceptoFacturacion (si aún no existe).
        - Calcula todos los importes.

        Después de guardar:
        - Recalcula automáticamente los totales del MovimientoCaja.
        """

        # Copiar la fotografía sólo la primera vez
        if self._state.adding:
            self.copiar_desde_concepto(
                self.concepto_facturacion
            )

        # Calcular importes
        self.calcular_importes()

        super().save(*args, **kwargs)

        # Actualizar el movimiento
        if self.movimiento_id:
            self.movimiento.recalcular_totales()
    
    @property
    def descripcion_prestaciones(self):

        detalles = self.detalles.order_by("orden")

        return "\n".join(
            f"{d.codigo} - {d.descripcion}"
            for d in detalles
        )
    
    def __str__(self):

        return f"{self.codigo} - {self.descripcion}"
    
    
class DetalleMedioPago(models.Model):

    movimiento = models.ForeignKey(
        MovimientoCaja,
        on_delete=models.CASCADE,
        related_name="detalles_medios_pago",
        verbose_name="Movimiento"
    )

    medio_pago = models.ForeignKey(
        MedioPago,
        on_delete=models.PROTECT,
        verbose_name="Medio de Pago"
    )

    importe = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Importe"
    )

    observacion = models.CharField(
        max_length=250,
        blank=True
    )

    orden = models.PositiveIntegerField(
        default=1
    )

    class Meta:

        ordering = [
            "orden",
            "id"
        ]

        verbose_name = "Detalle Medio de Pago"

        verbose_name_plural = "Detalles Medios de Pago"

    def __str__(self):

        return (
            f"{self.medio_pago} - ${self.importe}"
        )