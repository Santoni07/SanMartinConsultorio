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
            totalPrestacionesCalculado.toFixed(2);

    }

    const resumenPrestaciones =
        document.getElementById(
            "resumen_total_prestaciones"
        );

    if(resumenPrestaciones){

        resumenPrestaciones.innerHTML =
            "$ " +
            totalPrestacionesCalculado.toFixed(2);

    }

    // =====================================
    // TOTAL MEDIOS DE PAGO
    // =====================================

    if(totalMediosPago){

        totalMediosPago.innerHTML =
            "$ " +
            totalMediosCalculado.toFixed(2);

    }

    const resumenMedios =
        document.getElementById(
            "resumen_total_medios"
        );

    if(resumenMedios){

        resumenMedios.innerHTML =
            "$ " +
            totalMediosCalculado.toFixed(2);

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
            saldoPendiente.toFixed(2);

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
                saldoPendiente.toFixed(2);

        }

        else{

            estado.className =
                "text-danger fw-bold";

            estado.innerHTML =
                "✖ Exceso de $ " +
                Math.abs(
                    saldoPendiente
                ).toFixed(2);

        }

    }

    // =====================================
    // BOTÓN GUARDAR
    // =====================================

    const btnGuardar =
        document.getElementById(
            "btn_guardar_cobro"
        );

    if(btnGuardar){

        btnGuardar.disabled =
            (
                totalPrestacionesCalculado === 0 ||
                saldoPendiente !== 0
            );

    }

}