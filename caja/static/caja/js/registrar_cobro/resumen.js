// ======================================================
// RESUMEN
// ======================================================

function actualizarResumen(){

    // =====================================
    // VALOR TOTAL DE LAS PRESTACIONES
    // =====================================

    const totalPrestacionesCalculado =
        obtenerTotalPrestaciones();


    // =====================================
    // TOTAL A COBRAR AL PACIENTE
    // =====================================
    //
    // PARTICULAR:
    // paga el valor completo.
    //
    // OBRA SOCIAL SIN COSEGURO:
    // paga $0.
    //
    // OBRA SOCIAL CON COSEGURO:
    // paga solamente el coseguro.
    // =====================================

    let totalACobrarPaciente = 0;

    let totalCoseguros = 0;

    let hayObraSocial = false;

    let hayParticular = false;


    prestaciones.forEach(function(item){

        const cantidad =
            parseFloat(
                item.cantidad || 0
            );

        const importe =
            parseFloat(
                item.importe || 0
            );

        const subtotal =
            cantidad * importe;


        // =================================
        // PARTICULAR
        // =================================

        if(item.origen === "PARTICULAR"){

            hayParticular = true;

            totalACobrarPaciente +=
                subtotal;

        }


        // =================================
        // OBRA SOCIAL
        // =================================

        else if(item.origen === "OBRA_SOCIAL"){

            hayObraSocial = true;

            const tieneCoseguro =
                item.tiene_coseguro === true ||
                item.tiene_coseguro === "true" ||
                item.tiene_coseguro === 1 ||
                item.tiene_coseguro === "1";


            const importeCoseguro =
                parseFloat(
                    item.importe_coseguro || 0
                );


            if(tieneCoseguro){

                const subtotalCoseguro =
                    cantidad *
                    importeCoseguro;

                totalCoseguros +=
                    subtotalCoseguro;

                totalACobrarPaciente +=
                    subtotalCoseguro;

            }

        }

    });


    // =====================================
    // TOTAL A CARGO DE OBRA SOCIAL
    // =====================================

    const totalObraSocial =
        prestaciones.reduce(
            function(total, item){

                if(
                    item.origen !==
                    "OBRA_SOCIAL"
                ){
                    return total;
                }

                const cantidad =
                    parseFloat(
                        item.cantidad || 0
                    );

                const importe =
                    parseFloat(
                        item.importe || 0
                    );

                const coseguro =
                    parseFloat(
                        item.importe_coseguro || 0
                    );

                const tieneCoseguro =
                    item.tiene_coseguro === true ||
                    item.tiene_coseguro === "true" ||
                    item.tiene_coseguro === 1 ||
                    item.tiene_coseguro === "1";


                const subtotal =
                    cantidad *
                    importe;


                const subtotalCoseguro =
                    tieneCoseguro
                        ? cantidad * coseguro
                        : 0;


                return (
                    total +
                    subtotal -
                    subtotalCoseguro
                );

            },
            0
        );


    // =====================================
    // TOTAL MEDIOS DE PAGO
    // =====================================

    const totalMediosCalculado =
        obtenerTotalMediosPago();


    // =====================================
    // SALDO QUE DEBE PAGAR EL PACIENTE
    // =====================================

    const saldoPendiente =
        totalACobrarPaciente -
        totalMediosCalculado;


    // =====================================
    // TOTAL PRESTACIONES
    // =====================================

    if(totalPrestaciones){

        totalPrestaciones.innerHTML =
            "$ " +
            formatoMoneda(
                totalPrestacionesCalculado
            );

    }


    const resumenPrestaciones =
        document.getElementById(
            "resumen_total_prestaciones"
        );

    if(resumenPrestaciones){

        resumenPrestaciones.innerHTML =
            "$ " +
            formatoMoneda(
                totalPrestacionesCalculado
            );

    }


    // =====================================
    // TOTAL MEDIOS DE PAGO
    // =====================================

    if(totalMediosPago){

        totalMediosPago.innerHTML =
            "$ " +
            formatoMoneda(
                totalMediosCalculado
            );

    }


    const resumenMedios =
        document.getElementById(
            "resumen_total_medios"
        );

    if(resumenMedios){

        resumenMedios.innerHTML =
            "$ " +
            formatoMoneda(
                totalMediosCalculado
            );

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
            formatoMoneda(
                saldoPendiente
            );


        if(
            Math.abs(
                saldoPendiente
            ) < 0.01
        ){

            saldo.className =
                "text-success";

        }

        else if(
            saldoPendiente > 0
        ){

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

        // ---------------------------------
        // SIN PRESTACIONES
        // ---------------------------------

        if(
            prestaciones.length === 0
        ){

            estado.className =
                "text-secondary fw-bold";

            estado.innerHTML =
                "Aún no hay prestaciones cargadas.";

        }


        // ---------------------------------
        // OBRA SOCIAL SIN COSEGURO
        // ---------------------------------

        else if(
            hayObraSocial &&
            !hayParticular &&
            totalCoseguros === 0 &&
            totalMediosCalculado === 0
        ){

            estado.className =
                "text-primary fw-bold";

            estado.innerHTML =
                "✔ Prestación a cargo de la Obra Social";

        }


        // ---------------------------------
        // COSEGURO PENDIENTE
        // ---------------------------------

        else if(
            hayObraSocial &&
            totalCoseguros > 0 &&
            saldoPendiente > 0
        ){

            estado.className =
                "text-warning fw-bold";

            estado.innerHTML =
                "⚠ Coseguro a cobrar al paciente: $ " +
                formatoMoneda(
                    saldoPendiente
                );

        }


        // ---------------------------------
        // PAGO COMPLETO
        // ---------------------------------

        else if(
            Math.abs(
                saldoPendiente
            ) < 0.01
        ){

            estado.className =
                "text-success fw-bold";


            if(
                hayObraSocial &&
                totalCoseguros > 0
            ){

                estado.innerHTML =
                    "✔ Coseguro abonado completamente";

            }

            else{

                estado.innerHTML =
                    "✔ Pago Completo";

            }

        }


        // ---------------------------------
        // FALTA COBRAR
        // ---------------------------------

        else if(
            saldoPendiente > 0
        ){

            estado.className =
                "text-warning fw-bold";

            estado.innerHTML =
                "⚠ Faltan cobrar $ " +
                formatoMoneda(
                    saldoPendiente
                );

        }


        // ---------------------------------
        // EXCESO
        // ---------------------------------

        else{

            estado.className =
                "text-danger fw-bold";

            estado.innerHTML =
                "✖ Exceso de $ " +
                formatoMoneda(
                    Math.abs(
                        saldoPendiente
                    )
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


    if(btnGuardar){

        const hayPrestaciones =
            prestaciones.length > 0;


        const pagoCorrecto =
            Math.abs(
                saldoPendiente
            ) < 0.01;


        btnGuardar.disabled =
            (
                !hayPrestaciones ||
                !pagoCorrecto
            );

    }


    // =====================================
    // DEBUG TEMPORAL
    // =====================================

    console.log(
        "Total prestaciones:",
        totalPrestacionesCalculado
    );

    console.log(
        "A cargo OS:",
        totalObraSocial
    );

    console.log(
        "Coseguros:",
        totalCoseguros
    );

    console.log(
        "A cobrar paciente:",
        totalACobrarPaciente
    );

}