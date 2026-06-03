# turnos/utils/utils_turnos.py

from datetime import date
from turnos.models import Turnos


def actualizar_turnos_ausentes():

    turnos_vencidos = Turnos.objects.filter(
        estado='PENDIENTE',
        fecha__lt=date.today()
    )

    cantidad = turnos_vencidos.count()

    if cantidad:

        turnos_vencidos.update(
            estado='AUSENTE'
        )

    return cantidad