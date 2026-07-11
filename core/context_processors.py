from core.utils import (
    obtener_centro_activo,
    modo_colaboracion
)


def centro_activo(request):

    return {

        'centro_activo': obtener_centro_activo(request),

        'modo_colaboracion': modo_colaboracion(request),
        
         'modal_notificacion': request.session.pop(
            'modal_notificacion',
            None
        ),
        
        

    }
    