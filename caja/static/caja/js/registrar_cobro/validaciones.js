// ======================================================
// VALIDACIONES
// ======================================================

function validarFormulario(){

    const mensajes =
        document.getElementById("mensajes");

    if(mensajes){

        mensajes.innerHTML = "";

    }

    // =====================================
    // PRESTACIONES
    // =====================================

    if(prestaciones.length === 0){

        mostrarError(
            "Debe agregar al menos una prestación."
        );

        return false;

    }

    // =====================================
    // MEDIOS DE PAGO
    // =====================================

    const totalPrestaciones = obtenerTotalPrestaciones();

    if (
        totalPrestaciones > 0 &&
        obtenerSaldoPendiente() !== 0
    ) {

        mostrarError(
            "Debe completar los medios de pago."
        );

        return false;

    }

    // =====================================
    // CONTROL DE IMPORTES
    // =====================================

    const totalPrestaciones =
        obtenerTotalPrestaciones();

    const totalMedios =
        obtenerTotalMediosPago();

    const saldoPendiente =
        obtenerSaldoPendiente();

    if(saldoPendiente > 0.01){

        mostrarError(

            "El cobro no puede registrarse.<br><br>" +

            "<strong>Total Prestaciones:</strong> $" +
            totalPrestaciones.toFixed(2) +

            "<br>" +

            "<strong>Total Medios de Pago:</strong> $" +
            totalMedios.toFixed(2) +

            "<br><br>" +

            "<strong>Faltan cobrar:</strong> $" +
            saldoPendiente.toFixed(2)

        );

        return false;

    }

    if(saldoPendiente < -0.01){

        mostrarError(

            "El cobro no puede registrarse.<br><br>" +

            "<strong>Total Prestaciones:</strong> $" +
            totalPrestaciones.toFixed(2) +

            "<br>" +

            "<strong>Total Medios de Pago:</strong> $" +
            totalMedios.toFixed(2) +

            "<br><br>" +

            "<strong>Existe un excedente de:</strong> $" +
            Math.abs(saldoPendiente).toFixed(2)

        );

        return false;

    }

    return true;

}