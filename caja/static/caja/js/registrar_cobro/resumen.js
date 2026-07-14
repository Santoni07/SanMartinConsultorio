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

    // =====================================
    // TOTAL PRESTACIONES
    // =====================================

    if(totalPrestaciones){

        totalPrestaciones.innerHTML =
            "$ " +
            formatoMoneda(totalPrestacionesCalculado);

    }

    const resumenPrestaciones =
        document.getElementById(
            "resumen_total_prestaciones"
        );

    if(resumenPrestaciones){

        resumenPrestaciones.innerHTML =
            "$ " +
            formatoMoneda(totalPrestacionesCalculado);

    }

    // =====================================
    // TOTAL MEDIOS DE PAGO
    // =====================================

    if(totalMediosPago){

        totalMediosPago.innerHTML =
            "$ " +
            formatoMoneda(totalMediosCalculado);

    }

    const resumenMedios =
        document.getElementById(
            "resumen_total_medios"
        );

    if(resumenMedios){

        resumenMedios.innerHTML =
            "$ " +
            formatoMoneda(totalMediosCalculado);

    }

    // =====================================
    // SALDO PENDIENTE
    // =====================================

    const saldo =
        document.getElementById(
            "saldo_pendiente"
        );

    if(saldo){

        saldo.innerHTML =
            "$ " +
            formatoMoneda(saldoPendiente);

        if(saldoPendiente === 0){

            saldo.className =
                "text-success";

        }

        else if(saldoPendiente > 0){

            saldo.className =
                "text-warning";

        }

        else{

            saldo.className =
                "text-danger";

        }

    }

    // =====================================
    // ESTADO DEL PAGO
    // =====================================

    const estado =
        document.getElementById(
            "estado_pago"
        );

    if(estado){

        if(totalPrestacionesCalculado === 0){

            estado.className =
                "text-secondary fw-bold";

            estado.innerHTML =
                "Aún no hay prestaciones cargadas.";

        }

        else if(saldoPendiente === 0){

            estado.className =
                "text-success fw-bold";

            estado.innerHTML =
                "✔ Pago Completo";

        }

        else if(saldoPendiente > 0){

            estado.className =
                "text-warning fw-bold";

            estado.innerHTML =
                "⚠ Faltan cobrar $ " +
                formatoMoneda(saldoPendiente);

        }

        else{

            estado.className =
                "text-danger fw-bold";

            estado.innerHTML =
                "✖ Exceso de $ " +
                formatoMoneda(
                    Math.abs(saldoPendiente)
                );

        }

    }

    // =====================================
    // BOTÓN GUARDAR
    // =====================================

    const btnGuardar =
        document.getElementById(
            "btn_guardar_cobro"
        );

    if (btnGuardar) {

        const hayPrestaciones =
            prestaciones.length > 0;

        btnGuardar.disabled =
            (
                !hayPrestaciones ||
                saldoPendiente !== 0
            );

    }

}