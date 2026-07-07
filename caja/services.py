import json

from decimal import Decimal

from django.db import transaction

from .models import (
    MovimientoCaja,
    DetalleMovimientoCaja,
    HistorialMovimientoCaja,
    ConceptoFacturacion,
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