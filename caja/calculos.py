from decimal import Decimal


def calcular_detalle(concepto, cantidad=1, retencion=Decimal("0")):
    """
    Calcula todos los importes de una prestación.

    Retorna un diccionario con:
        importe
        iva
        neto
        medico
        consultorio
    """

    importe = concepto.importe_particular * cantidad

    iva = (
        importe *
        concepto.porcentaje_iva
    ) / Decimal("100")

    neto = (
        importe
        - iva
        - retencion
    )

    if concepto.tipo_calculo == "PORCENTAJE":

        medico = (
            neto *
            concepto.porcentaje_medico
        ) / Decimal("100")

        consultorio = (
            neto *
            concepto.porcentaje_consultorio
        ) / Decimal("100")

    else:

        medico = (
            concepto.honorario_fijo_medico
            * cantidad
        )

        consultorio = (
            neto
            - medico
        )

    return {

        "importe": importe,

        "iva": iva,

        "neto": neto,

        "medico": medico,

        "consultorio": consultorio,

    }