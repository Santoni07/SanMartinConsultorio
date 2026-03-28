import copy
from turnos.models import AgendaMedico, ExcepcionAgenda


def obtener_agenda_dia(medico, fecha):

    agenda = AgendaMedico.objects.filter(
        medico=medico,
        fecha=fecha
    ).first()

    excepcion = ExcepcionAgenda.objects.filter(
        medico=medico,
        fecha=fecha
    ).first()

    # 🔴 CERRADO
    if excepcion and excepcion.tipo == 'CERRADO':
        return None

    # 🟡 REPROGRAMAR
    if excepcion and excepcion.tipo == 'REPROGRAMAR':
        return None

    # 🟢 MODIFICADO (🔥 ESTO TE FALTABA)
    if excepcion and excepcion.tipo == 'MODIFICADO':

        if agenda:
            agenda_modificada = copy.copy(agenda)

            agenda_modificada.hora_inicio = excepcion.hora_inicio
            agenda_modificada.hora_fin = excepcion.hora_fin

            return agenda_modificada

    return agenda