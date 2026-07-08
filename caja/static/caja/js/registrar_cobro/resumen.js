// ======================================================
// RESUMEN
// ======================================================

function actualizarResumen(){

    const totalPrestacionesCalculado =
        obtenerTotalPrestaciones();

    const totalMediosCalculado =
        obtenerTotalMediosPago();

    const saldoPendiente =
        obtenerSaldoPendiente();

    if(totalPrestaciones){

        totalPrestaciones.innerHTML =
            "$ " +
            totalPrestacionesCalculado.toFixed(2);

    }

    if(totalMediosPago){

        totalMediosPago.innerHTML =
            "$ " +
            totalMediosCalculado.toFixed(2);

    }

    const saldo =
        document.getElementById(
            "saldo_pendiente"
        );

    if(saldo){

        saldo.innerHTML =
            "$ " +
            saldoPendiente.toFixed(2);

    }

}