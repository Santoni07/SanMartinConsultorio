// ======================================================
// CONSTANCIA DE PRESTACIÓN - OBRA SOCIAL
// ======================================================

function inicializarConstanciaPrestacion(){

    const boton =
        document.getElementById(
            "btn_imprimir_constancia"
        );

    const formulario =
        document.getElementById(
            "form_registrar_cobro"
        );

    const turno =
        document.getElementById(
            "id_turno"
        );

    const tipoCobertura =
        document.getElementById(
            "tipo_cobertura"
        );

    const detallesJson =
        document.getElementById(
            "detalles_json"
        );


    if(
        !boton ||
        !formulario ||
        !turno ||
        !tipoCobertura ||
        !detallesJson
    ){

        console.error(
            "No se pudieron inicializar los controles de la constancia."
        );

        return;
    }


    // ==================================================
    // ACTUALIZAR BOTÓN
    // ==================================================

    window.actualizarBotonConstancia = function(){

        const hayTurno =
            turno.value !== "";

        const hayPrestaciones =
            typeof prestaciones !== "undefined" &&
            Array.isArray(prestaciones) &&
            prestaciones.length > 0;

        const esObraSocial =
            tipoCobertura.value === "OBRA_SOCIAL";


        console.log(
            "CONSTANCIA:",
            {
                turno: turno.value,
                cobertura: tipoCobertura.value,
                prestaciones:
                    typeof prestaciones !== "undefined"
                        ? prestaciones.length
                        : "NO DEFINIDO",
                hayTurno: hayTurno,
                hayPrestaciones: hayPrestaciones,
                esObraSocial: esObraSocial
            }
        );


        boton.disabled = !(
            hayTurno &&
            hayPrestaciones &&
            esObraSocial
        );

    };


    // ==================================================
    // IMPRIMIR
    // ==================================================

    boton.addEventListener(
        "click",
        function(){

            if(boton.disabled){
                return;
            }


            // ==========================================
            // ACTUALIZAR PRESTACIONES
            // ==========================================

            detallesJson.value =
                JSON.stringify(prestaciones);


            // ==========================================
            // GUARDAR CONFIGURACIÓN ORIGINAL
            // ==========================================

            const actionOriginal =
                formulario.getAttribute("action");

            const targetOriginal =
                formulario.getAttribute("target");


            // ==========================================
            // ENVIAR A CONSTANCIA
            // ==========================================

            formulario.setAttribute(
                "action",
                "/caja/constancia-prestacion/"
            );

            formulario.setAttribute(
                "target",
                "_blank"
            );

            formulario.submit();


            // ==========================================
            // RESTAURAR ACTION
            // ==========================================

            if(actionOriginal){

                formulario.setAttribute(
                    "action",
                    actionOriginal
                );

            }
            else{

                formulario.removeAttribute(
                    "action"
                );

            }


            // ==========================================
            // RESTAURAR TARGET
            // ==========================================

            if(targetOriginal){

                formulario.setAttribute(
                    "target",
                    targetOriginal
                );

            }
            else{

                formulario.removeAttribute(
                    "target"
                );

            }

        }
    );


    // ==================================================
    // CAMBIO DE TURNO
    // ==================================================

    turno.addEventListener(
        "change",
        function(){

            window.actualizarBotonConstancia();

        }
    );


    // ==================================================
    // ESTADO INICIAL
    // ==================================================

    window.actualizarBotonConstancia();

}