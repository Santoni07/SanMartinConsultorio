from django.db import models
from nomenclador.models import NomencladorGeneral

# Create your models here.

class ObraSocial(models.Model):

    nombre = models.CharField(
        "Nombre",
        max_length=150,
        unique=True
    )

    sigla = models.CharField(
        "Sigla",
        max_length=20,
        blank=True,
        unique=True,
        null=True
    )

    codigo = models.CharField(
        "Código",
        max_length=20,
        unique=True,
        blank=True,
        
        null=True
    )

    cuit = models.CharField(
        "CUIT",
        max_length=13,
        blank=True
    )

    telefono = models.CharField(
        "Teléfono",
        max_length=50,
        blank=True
    )

    email = models.EmailField(
        "Email",
        blank=True
    )

    domicilio = models.CharField(
        "Domicilio",
        max_length=250,
        blank=True
    )

    ciudad = models.CharField(
        "Ciudad",
        max_length=100,
        blank=True
    )

    provincia = models.CharField(
        "Provincia",
        max_length=100,
        blank=True
    )

    observaciones = models.TextField(
        "Observaciones",
        blank=True
    )

    activa = models.BooleanField(
        "Activa",
        default=True
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )
    
    sitio_web = models.URLField(
    "Sitio Web",
    blank=True
    )

    portal_prestadores = models.URLField(
        "Portal de Prestadores",
        blank=True
    )

    portal_autorizaciones = models.URLField(
        "Portal de Autorizaciones",
        blank=True
    )

    portal_afiliados = models.URLField(
        "Portal de Afiliados",
        blank=True
    )

    cartilla_online = models.URLField(
        "Cartilla Médica Online",
        blank=True
    )

    credenciales_online = models.URLField(
        "Descarga de Credenciales",
        blank=True
    )

    observaciones_portal = models.TextField(
        "Observaciones del Portal",
        blank=True
    )
    
    usa_planes = models.BooleanField(
        "¿Utiliza planes?",
        default=False
    )
    es_particular = models.BooleanField(
        default=False,
        verbose_name="Es Particular"
    )

    class Meta:

        ordering = [
            "nombre"
        ]

        verbose_name = "Obra Social"

        verbose_name_plural = "Obras Sociales"

    def __str__(self):
        return self.nombre
    


# ==========================================================
# PLANES DE OBRAS SOCIALES
# ==========================================================

class PlanObraSocial(models.Model):

    obra_social = models.ForeignKey(
        ObraSocial,
        on_delete=models.CASCADE,
        related_name="planes",
        verbose_name="Obra Social"
    )

    codigo = models.CharField(
        "Código",
        max_length=30
    )

    nombre = models.CharField(
        "Nombre",
        max_length=150
    )

    observaciones = models.TextField(
        "Observaciones",
        blank=True
    )

    orden = models.PositiveIntegerField(
        "Orden",
        default=0
    )

    activo = models.BooleanField(
        "Activo",
        default=True
    )

    fecha_alta = models.DateTimeField(
        "Fecha de alta",
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        "Última modificación",
        auto_now=True
    )

    class Meta:

        verbose_name = "Plan"

        verbose_name_plural = "Planes"

        ordering = [
            "orden",
            "codigo",
            "nombre"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "obra_social",
                    "codigo"
                ],
                name="plan_codigo_unico_por_obra_social"
            )

        ]

    def __str__(self):

        if self.codigo:
            return f"{self.obra_social.sigla} - {self.codigo} - {self.nombre}"

        return f"{self.obra_social.sigla} - {self.nombre}"
    
# ==========================================================
# PRESTACIONES DEL PLAN
# ==========================================================

class PrestacionPlan(models.Model):

    ESTADOS = [
        ("ACTIVA", "Activa"),
        ("INACTIVA", "Inactiva"),
    ]

    obra_social = models.ForeignKey(
        ObraSocial,
        on_delete=models.CASCADE,
        related_name="prestaciones"
    )

    plan = models.ForeignKey(
        PlanObraSocial,
        on_delete=models.CASCADE,
        related_name="prestaciones",
        null=True,
        blank=True
    )

    nomenclador = models.ForeignKey(
        NomencladorGeneral,
        on_delete=models.PROTECT,
        related_name="prestaciones_convenio"
    )

    valor = models.DecimalField(
        "Valor Convenio",
        max_digits=12,
        decimal_places=2
    )
    
    tiene_coseguro = models.BooleanField(
        default=False,
        verbose_name="Tiene coseguro"
    )

    importe_coseguro = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Importe Coseguro"
    )
    
    # ==========================================================
    # COPAGO
    # ==========================================================

    tiene_copago = models.BooleanField(
        default=False,
        verbose_name="Tiene copago"
    )

    importe_copago = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Importe Copago"
    )

    fecha_vigencia_desde = models.DateField()

    fecha_vigencia_hasta = models.DateField(
        blank=True,
        null=True
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="ACTIVA"
    )

    observaciones = models.TextField(
        blank=True
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        auto_now=True
    )
    
    porcentaje_iva = models.DecimalField(
    max_digits=5,
    decimal_places=2,
    default=0
    )

    TIPOS_CALCULO = [
        ('PORCENTAJE', 'Porcentaje'),
        ('FIJO_MEDICO', 'Honorario fijo médico'),
    ]

    tipo_calculo = models.CharField(
        max_length=20,
        choices=TIPOS_CALCULO,
        default='PORCENTAJE'
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

    proveedor = models.ForeignKey(
        'proveedores.Proveedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prestaciones_obras_sociales"
    )

    importe_proveedor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Importe Proveedor"
    )
        

    class Meta:

        verbose_name = "Prestación"

        verbose_name_plural = "Prestaciones"

        ordering = [
            "nomenclador__codigo"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "obra_social",
                    "plan",
                    "nomenclador"
                ],
                name="prestacion_unica_por_convenio"
            )

        ]

    def __str__(self):

        if self.plan:
            return f"{self.obra_social} - {self.plan.nombre} - {self.nomenclador.codigo}"

        return f"{self.obra_social} - {self.nomenclador.codigo}"



class PrestacionPlanValor(models.Model):

    prestacion = models.ForeignKey(
        PrestacionPlan,
        on_delete=models.CASCADE,
        related_name="valores"
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    vigente_desde = models.DateField()

    vigente_hasta = models.DateField(
        blank=True,
        null=True
    )

    activo = models.BooleanField(
        default=True
    )

    fecha_alta = models.DateTimeField(
        auto_now_add=True
    )
    moneda = models.CharField(

        max_length=10,

        default="ARS"

    )
    class Meta:

        ordering = [
            "-vigente_desde"
        ]
 
 
# ==========================================================
# MASTER DE OBRA SOCIAL
# ==========================================================

class MasterObraSocial(models.Model):

    # ======================================================
    # ESTADOS
    # ======================================================

    ESTADOS = [
        ("BORRADOR", "Borrador"),
        ("PRESENTADO", "Presentado"),
        ("COBRADO", "Cobrado"),
        ("ANULADO", "Anulado"),
    ]

    # ======================================================
    # OBRA SOCIAL / PERÍODO
    # ======================================================

    obra_social = models.ForeignKey(
        ObraSocial,
        on_delete=models.PROTECT,
        related_name="masters",
        verbose_name="Obra Social"
    )

    anio = models.PositiveIntegerField(
        "Año"
    )

    mes = models.PositiveSmallIntegerField(
        "Mes"
    )

    # ======================================================
    # ESTADO DEL MASTER
    # ======================================================

    estado = models.CharField(
        "Estado",
        max_length=15,
        choices=ESTADOS,
        default="BORRADOR"
    )

    # ======================================================
    # PRESENTACIÓN
    # ======================================================

    fecha_presentacion = models.DateField(
        "Fecha de presentación",
        null=True,
        blank=True
    )

    numero_presentacion = models.CharField(
        "Número de presentación",
        max_length=50,
        blank=True
    )

    numero_factura = models.CharField(
        "Número de factura",
        max_length=50,
        blank=True
    )

    # ======================================================
    # COBRO
    # ======================================================

    fecha_cobro = models.DateField(
        "Fecha de cobro",
        null=True,
        blank=True
    )

    # ======================================================
    # OBSERVACIONES
    # ======================================================

    observaciones = models.TextField(
        "Observaciones",
        blank=True
    )

    # ======================================================
    # AUDITORÍA
    # ======================================================

    creado_por = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="masters_obra_social_creados",
        verbose_name="Creado por"
    )

    fecha_creacion = models.DateTimeField(
        "Fecha de creación",
        auto_now_add=True
    )

    fecha_modificacion = models.DateTimeField(
        "Última modificación",
        auto_now=True
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:

        verbose_name = "Master de Obra Social"

        verbose_name_plural = "Masters de Obras Sociales"

        ordering = [
            "-anio",
            "-mes",
            "obra_social__nombre"
        ]

        constraints = [

            # Una OS solamente puede tener
            # un Master por mes/año.
            models.UniqueConstraint(
                fields=[
                    "obra_social",
                    "anio",
                    "mes"
                ],
                name="master_unico_por_os_periodo"
            ),

            # Mes válido: 1 a 12.
            models.CheckConstraint(
            check=models.Q(
                mes__gte=1,
                mes__lte=12
            ),
            name="master_mes_valido"
        ),

        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        return (
            f"{self.obra_social.nombre} - "
            f"{self.mes:02d}/{self.anio}"
        )
        
# ==========================================================
# DETALLE MASTER DE OBRA SOCIAL
# ==========================================================

class DetalleMasterObraSocial(models.Model):

    # ======================================================
    # ESTADO DE AUDITORÍA DE LA PRESTACIÓN
    # ======================================================

    ESTADOS = [
        ("PENDIENTE", "Pendiente de auditoría"),
        ("ACEPTADO", "Aceptado"),
        ("DEBITO_PARCIAL", "Débito parcial"),
        ("RECHAZADO", "Rechazado"),
    ]

    # ======================================================
    # ESTADO DE REFACTURACIÓN
    # ======================================================

    ESTADOS_REFACTURACION = [
        ("NO_APLICA", "No aplica"),
        ("PENDIENTE", "Pendiente de refacturación"),
        ("PRESENTADA", "Refacturación presentada"),
        ("ACEPTADA", "Refacturación aceptada"),
        ("RECHAZADA", "Refacturación rechazada"),
    ]

    # ======================================================
    # MASTER
    # ======================================================

    master = models.ForeignKey(
        MasterObraSocial,
        on_delete=models.CASCADE,
        related_name="detalles",
        verbose_name="Master"
    )

    # ======================================================
    # PRESTACIÓN REALIZADA
    # ======================================================

    detalle_movimiento = models.OneToOneField(
        "caja.DetalleMovimientoCaja",
        on_delete=models.PROTECT,
        related_name="detalle_master_obra_social",
        verbose_name="Prestación"
    )

    # ======================================================
    # ESTADO DE AUDITORÍA
    # ======================================================

    estado = models.CharField(
        "Estado",
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    # ======================================================
    # IMPORTE PRESENTADO
    #
    # Se guarda el importe histórico que fue presentado
    # a la Obra Social.
    #
    # No debemos depender del valor actual del nomenclador
    # porque los aranceles pueden cambiar posteriormente.
    # ======================================================

    importe_presentado = models.DecimalField(
        "Importe presentado",
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ======================================================
    # IMPORTE RECONOCIDO
    #
    # Importe que la Obra Social reconoce luego de realizar
    # la auditoría.
    # ======================================================

    importe_reconocido = models.DecimalField(
        "Importe reconocido",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ======================================================
    # IMPORTE DEBITADO
    #
    # Diferencia entre lo presentado y lo reconocido.
    #
    # Ejemplo:
    #
    # Presentado:  $30.000
    # Reconocido:  $20.000
    # Debitado:    $10.000
    # ======================================================

    importe_debitado = models.DecimalField(
        "Importe debitado",
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ======================================================
    # MOTIVO DEL DÉBITO / RECHAZO
    # ======================================================

    motivo_debito = models.TextField(
        "Motivo del débito / rechazo",
        blank=True
    )

    # ======================================================
    # REFACTURABLE
    #
    # Indica si la prestación debitada o rechazada puede
    # volver a presentarse ante la Obra Social.
    # ======================================================

    refacturable = models.BooleanField(
        "¿Es refacturable?",
        default=False
    )

    # ======================================================
    # ESTADO DE REFACTURACIÓN
    # ======================================================

    estado_refacturacion = models.CharField(
        "Estado de refacturación",
        max_length=20,
        choices=ESTADOS_REFACTURACION,
        default="NO_APLICA"
    )

    # ======================================================
    # FECHA DE REFACTURACIÓN
    # ======================================================

    fecha_refacturacion = models.DateField(
        "Fecha de refacturación",
        null=True,
        blank=True
    )

    # ======================================================
    # OBSERVACIONES DE REFACTURACIÓN
    # ======================================================

    observacion_refacturacion = models.TextField(
        "Observación de refacturación",
        blank=True
    )

    # ======================================================
    # OBSERVACIONES GENERALES
    # ======================================================

    observaciones = models.TextField(
        "Observaciones",
        blank=True
    )

    # ======================================================
    # AUDITORÍA / TRAZABILIDAD
    # ======================================================

    fecha_incorporacion = models.DateTimeField(
        "Fecha de incorporación",
        auto_now_add=True
    )

    fecha_resolucion = models.DateField(
        "Fecha de resolución",
        null=True,
        blank=True
    )

    # ======================================================
    # CONFIGURACIÓN
    # ======================================================

    class Meta:

        verbose_name = "Detalle Master de Obra Social"

        verbose_name_plural = "Detalles Master de Obra Social"

        ordering = [
            "detalle_movimiento__fecha_prestacion",
            "id"
        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        return (
            f"{self.master} - "
            f"{self.detalle_movimiento.codigo} - "
            f"{self.detalle_movimiento.descripcion}"
        )