from core.models import CentroMedico


def obtener_centro_activo(request):

    centro_id = request.session.get('centro_id')

    if centro_id:

        return CentroMedico.objects.filter(
            id=centro_id
        ).first()

    return CentroMedico.objects.first()

def modo_colaboracion(request):

    if not request.user.is_authenticated:
        return False

    try:

        perfil = request.user.perfilusuario

        centro_activo = obtener_centro_activo(request)

        if not perfil.centro_principal:
            return False

        return (
            centro_activo
            and
            perfil.centro_principal.id != centro_activo.id
        )

    except:
        return False
    


def mostrar_notificacion(
    request,
    *,
    tipo="success",
    titulo="Operación realizada",
    mensaje="La operación se realizó correctamente.",
    icono="bi-check-circle-fill",
    color="success",
    detalles=None,
):

    from django.utils import timezone

    request.session["modal_notificacion"] = {

        "tipo": tipo,

        "titulo": titulo,

        "mensaje": mensaje,

        "icono": icono,

        "color": color,

        "detalles": detalles or [],

        "fecha": timezone.now().isoformat(),

    }
    
def mostrar_exito(
    request,
    titulo,
    mensaje,
    icono="bi-check-circle-fill",
    detalles=None,
):

    mostrar_notificacion(

        request,

        tipo="success",

        titulo=titulo,

        mensaje=mensaje,

        icono=icono,

        color="success",

        detalles=detalles,

    )


def mostrar_error(
    request,
    titulo,
    mensaje,
    detalles=None,
):

    mostrar_notificacion(

        request,

        tipo="danger",

        titulo=titulo,

        mensaje=mensaje,

        icono="bi-x-circle-fill",

        color="danger",

        detalles=detalles,

    )


def mostrar_info(
    request,
    titulo,
    mensaje,
    detalles=None,
):

    mostrar_notificacion(

        request,

        tipo="info",

        titulo=titulo,

        mensaje=mensaje,

        icono="bi-info-circle-fill",

        color="info",

        detalles=detalles,

    )


def mostrar_advertencia(
    request,
    titulo,
    mensaje,
    detalles=None,
):

    mostrar_notificacion(

        request,

        tipo="warning",

        titulo=titulo,

        mensaje=mensaje,

        icono="bi-exclamation-triangle-fill",

        color="warning",

        detalles=detalles,

    )