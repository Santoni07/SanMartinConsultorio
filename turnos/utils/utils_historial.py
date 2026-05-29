from turnos.models import HistorialTurno


def registrar_historial_turno(
    turno,
    accion,
    usuario=None,
    sede_operacion=None,
    descripcion='',
    datos_anteriores=None,
    datos_nuevos=None
):

    HistorialTurno.objects.create(

        turno=turno,

        accion=accion,

        usuario=usuario,

        sede_operacion=sede_operacion,

        descripcion=descripcion,

        datos_anteriores=datos_anteriores,

        datos_nuevos=datos_nuevos
    )