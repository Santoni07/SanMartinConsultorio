
// ======================================================
// VALIDACIONES
// ======================================================

function validarFormulario(){

    const mensajes =
    document.getElementById("mensajes");

    if(mensajes){

        mensajes.innerHTML = "";

    }
    if(prestaciones.length === 0){

        mostrarError(
            "Debe agregar al menos una prestación."
        );

        return false;

    }

    if(mediosPago.length === 0){

        mostrarError(
            "Debe agregar al menos un medio de pago."
        );

        return false;

    }

    if(Math.abs(obtenerSaldoPendiente()) > 0.01){

        mostrarError(
            "La suma de los medios de pago debe coincidir con el total del cobro."
        );

        return false;

    }

    return true;

}