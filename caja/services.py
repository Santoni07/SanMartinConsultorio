import json

from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.db import transaction

from .models import (
    MovimientoCaja,
    DetalleMovimientoCaja,
    HistorialMovimientoCaja,
    ConceptoFacturacion,
    DetalleMedioPago,
)

from .calculos import calcular_detalle

class CobroService:

    def __init__(
        self,
        request,
        form,
        caja,
        centro_medico,
    ):

        self.request = request

        self.form = form

        self.caja = caja

        self.centro_medico = centro_medico

        self.turno = form.cleaned_data["turno"]

        self.detalles = []

        self.movimiento = None

        self.total_importe = Decimal("0")

        self.total_bruto = Decimal("0")

        self.total_iva = Decimal("0")

        self.total_neto = Decimal("0")

        self.total_medico = Decimal("0")

        self.total_consultorio = Decimal("0")
        



# ==========================================================
# CIERRE DE CAJA
# ==========================================================

class CierreCajaService:

    def __init__(self, caja):

        self.caja = caja

        self.movimientos = None
        self.movimientos_pdf = []

        self.total_bruto = Decimal("0")
        self.total_iva = Decimal("0")
        self.total_neto = Decimal("0")
        self.total_medico = Decimal("0")
        self.total_consultorio = Decimal("0")
        self.total_retenciones = Decimal("0")

        self.efectivo_a_rendir = Decimal("0")

        self.resumen_medios = []

        self.cantidad_movimientos = 0
        self.cantidad_prestaciones = 0
        self.cantidad_pacientes = 0

    # ======================================================
    # MÉTODO PRINCIPAL
    # ======================================================

    def obtener_datos(self):

        self._leer_movimientos()

        self._calcular_totales()

        self._calcular_estadisticas()

        self._calcular_medios_pago()
        
        self._preparar_movimientos_pdf()

        return {

            "caja": self.caja,

            "movimientos": self.movimientos_pdf,

            "resumen_medios": self.resumen_medios,

            "cantidad_movimientos": self.cantidad_movimientos,

            "cantidad_prestaciones": self.cantidad_prestaciones,

            "cantidad_pacientes": self.cantidad_pacientes,

            "total_bruto": self.total_bruto,

            "total_iva": self.total_iva,

            "total_neto": self.total_neto,

            "total_medico": self.total_medico,

            "total_consultorio": self.total_consultorio,

            "total_retenciones": self.total_retenciones,

            "efectivo_a_rendir": self.efectivo_a_rendir,

        }

    # ======================================================
    # MOVIMIENTOS
    # ======================================================

    def _leer_movimientos(self):

        self.movimientos = (
            MovimientoCaja.objects.filter(
                caja=self.caja,
                estado="ACTIVO",
            )
            .select_related(
                "paciente",
                "creado_por",
                "turno",
            )
            .prefetch_related(
                "detalles",
                "detalles_medios_pago__medio_pago",
            )
            .order_by(
                "fecha_creacion",
                "id",
            )
        )

    # ======================================================
    # TOTALES
    # ======================================================

    def _calcular_totales(self):

        totales = self.movimientos.aggregate(

            bruto=Sum("importe_bruto"),

            iva=Sum("importe_iva"),

            neto=Sum("importe_neto"),

            medico=Sum("importe_medico"),

            consultorio=Sum("importe_consultorio"),

            retenciones=Sum("retencion_monto"),

        )

        self.total_bruto = (
            totales["bruto"] or Decimal("0")
        )

        self.total_iva = (
            totales["iva"] or Decimal("0")
        )

        self.total_neto = (
            totales["neto"] or Decimal("0")
        )

        self.total_medico = (
            totales["medico"] or Decimal("0")
        )

        self.total_consultorio = (
            totales["consultorio"] or Decimal("0")
        )

        self.total_retenciones = (
            totales["retenciones"] or Decimal("0")
        )

    # ======================================================
    # ESTADÍSTICAS
    # ======================================================

    def _calcular_estadisticas(self):

        self.cantidad_movimientos = self.movimientos.count()

        self.cantidad_prestaciones = (
            DetalleMovimientoCaja.objects.filter(
                movimiento__caja=self.caja,
                movimiento__estado="ACTIVO",
            ).count()
        )

        self.cantidad_pacientes = (
            self.movimientos.exclude(
                paciente=None
            )
            .values("paciente")
            .distinct()
            .count()
        )

    # ======================================================
    # MEDIOS DE PAGO
    # ======================================================

    def _calcular_medios_pago(self):

        resumen = (
            DetalleMedioPago.objects.filter(
                movimiento__caja=self.caja,
                movimiento__estado="ACTIVO",
            )
            .values(
                "medio_pago__nombre"
            )
            .annotate(
                cantidad=Count("id"),
                total=Sum("importe"),
            )
            .order_by(
                "medio_pago__nombre"
            )
        )

        self.resumen_medios = list(resumen)

        efectivo = next(
            (
                item
                for item in self.resumen_medios
                if item["medio_pago__nombre"].lower() == "efectivo"
            ),
            None,
        )

        if efectivo:

            self.efectivo_a_rendir = efectivo["total"]

        else:

            self.efectivo_a_rendir = Decimal("0")
            
    # ======================================================
    # MOVIMIENTOS PARA PDF
    # ======================================================

    def _preparar_movimientos_pdf(self):

        self.movimientos_pdf = []

        for movimiento in self.movimientos:

            prestaciones = []

            for detalle in movimiento.detalles.all():

                prestaciones.append({

                    "codigo": detalle.codigo,

                    "descripcion": detalle.descripcion,

                    "cantidad": detalle.cantidad,

                    "importe": detalle.importe,

                })

            medios = []

            for medio in movimiento.detalles_medios_pago.all():

                medios.append({

                    "medio": medio.medio_pago.nombre,

                    "importe": medio.importe,

                })

            self.movimientos_pdf.append({

                "id": movimiento.id,

                "hora": movimiento.fecha_creacion.strftime("%H:%M"),

                "paciente": (
                    str(movimiento.paciente)
                    if movimiento.paciente
                    else "-"
                ),

                "usuario": movimiento.creado_por.username,

                "prestaciones": prestaciones,

                "medios": medios,

                "bruto": movimiento.importe_bruto,

                "iva": movimiento.importe_iva,

                "neto": movimiento.importe_neto,

                "medico": movimiento.importe_medico,

                "consultorio": movimiento.importe_consultorio,

                "retencion": movimiento.retencion_monto,

            })


@transaction.atomic
def procesar(self):

    self._leer_detalles()

    self._crear_movimiento()

    self._crear_detalles()

    self._actualizar_movimiento()

    self._crear_historial()

    return self.movimiento

def _leer_detalles(self):

    detalles_json = self.request.POST.get(
        "detalles_json"
    )

    if not detalles_json:

        raise ValueError(
            "No se recibieron prestaciones."
        )

    self.detalles = json.loads(
        detalles_json
    )

    if not self.detalles:

        raise ValueError(
            "Debe seleccionar prestaciones."
        )
        
def _crear_movimiento(self):

    movimiento = self.form.save(
        commit=False
    )

    movimiento.caja = self.caja

    movimiento.centro_medico = (
        self.centro_medico
    )

    movimiento.turno = self.turno

    movimiento.paciente = (
        self.turno.paciente
    )

    movimiento.tipo = "INGRESO"

    movimiento.creado_por = (
        self.request.user
    )

    movimiento.estado = "ACTIVO"

    movimiento.concepto = (
        "Cobro de prestaciones"
    )

    movimiento.importe = 0

    movimiento.importe_bruto = 0

    movimiento.importe_iva = 0

    movimiento.importe_neto = 0

    movimiento.importe_medico = 0

    movimiento.importe_consultorio = 0

    movimiento.save()

    self.movimiento = movimiento
    
def _crear_detalles(self):

    orden = 1

    ultimo_concepto = None

    for item in self.detalles:

        concepto = ConceptoFacturacion.objects.select_related(
            "nomenclador"
        ).get(
            pk=item["id"]
        )

        ultimo_concepto = concepto

        cantidad = int(item["cantidad"])

        datos = calcular_detalle(
            concepto=concepto,
            cantidad=cantidad
        )

        DetalleMovimientoCaja.objects.create(

            movimiento=self.movimiento,

            concepto_facturacion=concepto,

            fecha_prestacion=self.turno.fecha,

            cantidad=cantidad,

            importe=datos["importe"],

            importe_iva=datos["iva"],

            importe_neto=datos["neto"],

            importe_medico=datos["medico"],

            importe_consultorio=datos["consultorio"],

            orden=orden,

        )

        self.total_importe += datos["importe"]

        self.total_bruto += datos["importe"]

        self.total_iva += datos["iva"]

        self.total_neto += datos["neto"]

        self.total_medico += datos["medico"]

        self.total_consultorio += datos["consultorio"]

        orden += 1

    self.ultimo_concepto = ultimo_concepto
    
def _actualizar_movimiento(self):

    self.movimiento.importe = self.total_importe

    self.movimiento.importe_bruto = self.total_bruto

    self.movimiento.importe_iva = self.total_iva

    self.movimiento.importe_neto = self.total_neto

    self.movimiento.importe_medico = self.total_medico

    self.movimiento.importe_consultorio = self.total_consultorio

    if len(self.detalles) == 1:

        self.movimiento.concepto_facturacion = (
            self.ultimo_concepto
        )

        self.movimiento.concepto = (
            f"{self.ultimo_concepto.nomenclador.codigo} - "
            f"{self.ultimo_concepto.nomenclador.descripcion}"
        )

    else:

        self.movimiento.concepto_facturacion = None

        self.movimiento.concepto = (
            f"{len(self.detalles)} prestaciones"
        )

    self.movimiento.save()