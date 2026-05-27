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