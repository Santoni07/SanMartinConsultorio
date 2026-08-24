// ======================================================
// PRESTACIONES
// ======================================================

function inicializarPrestaciones(){

    btnAgregarPrestacion = document.getElementById(
        "btn_agregar_prestacion"
    );

    selectPrestacion = document.getElementById(
        "id_concepto_facturacion"
    );

    inputImporte = document.getElementById(
        "id_importe_particular"
    );

    tablaPrestaciones = document.querySelector(
        "#tabla_prestaciones tbody"
    );

    totalPrestaciones = document.getElementById(
        "total_general"
    );

    detallesJson = document.getElementById(
        "detalles_json"
    );

    if(
        !btnAgregarPrestacion ||
        !selectPrestacion ||
        !inputImporte ||
        !tablaPrestaciones ||
        !totalPrestaciones ||
        !detallesJson
    ){
        return;
    }


    // =====================================
    // HABILITAR BOTÓN
    // =====================================

    btnAgregarPrestacion.disabled = true;

    selectPrestacion.addEventListener(
        "change",
        function(){

            btnAgregarPrestacion.disabled =
                (this.value === "");

        }
    );


    // =====================================
    // AGREGAR PRESTACIÓN
    // =====================================

    btnAgregarPrestacion.addEventListener(
        "click",
        function(){

            if(!selectPrestacion.value){

                mostrarError(
                    "Debe seleccionar una prestación."
                );

                return;
            }


            // =====================================
            // OBTENER OPCIÓN SELECCIONADA
            // =====================================

            const opcionSeleccionada =
                selectPrestacion.options[
                    selectPrestacion.selectedIndex
                ];


            const origen =
                opcionSeleccionada.dataset.origen;


            // =====================================
            // COSEGURO
            // =====================================

            const tieneCoseguro =
                opcionSeleccionada.dataset.tieneCoseguro === "1";


            const importeCoseguro =
                parseFloat(
                    opcionSeleccionada.dataset.importeCoseguro || 0
                );


            // =====================================
            // COPAGO
            // =====================================

            const tieneCopago =
                opcionSeleccionada.dataset.tieneCopago === "1";


            const importeCopago =
                parseFloat(
                    opcionSeleccionada.dataset.importeCopago || 0
                );


            // =====================================
            // VALIDAR ORIGEN
            // =====================================

            if(!origen){

                mostrarError(
                    "No se pudo determinar el origen de la prestación."
                );

                return;
            }


            // =====================================
            // IMPORTE
            // =====================================

            const importe =
                parseFloat(
                    inputImporte.value || 0
                );


            if(importe < 0){

                mostrarError(
                    "El importe de la prestación no puede ser negativo."
                );

                return;
            }


            // =====================================
            // CONTROLAR PRESTACIÓN REPETIDA
            // =====================================

            const existente =
                prestaciones.find(
                    p =>
                        p.id == selectPrestacion.value &&
                        p.origen == origen
                );


            if(existente){

                existente.cantidad++;


                mostrarAdvertencia(
                    "La prestación ya estaba agregada. " +
                    "Se incrementó la cantidad."
                );


                renderPrestaciones();


                // ===============================
                // LIMPIAR CONTROLES
                // ===============================

                selectPrestacion.selectedIndex = 0;

                inputImporte.value = "";

                btnAgregarPrestacion.disabled = true;

                selectPrestacion.focus();

                return;
            }


            // =====================================
            // DATOS DE LA PRESTACIÓN
            // =====================================

            const texto =
                opcionSeleccionada.text;


            const partes =
                texto.split(" - ");


            // =====================================
            // AGREGAR AL ARRAY
            // =====================================

            prestaciones.push({

                id: selectPrestacion.value,

                origen: origen,

                codigo: partes[0],

                descripcion:
                    partes.slice(1).join(" - "),

                cantidad: 1,


                // =================================
                // VALOR TOTAL PRESTACIÓN
                // =================================

                importe: importe,


                // =================================
                // COSEGURO
                // =================================

                tiene_coseguro:
                    tieneCoseguro,

                importe_coseguro:
                    importeCoseguro,


                // =================================
                // COPAGO
                // =================================

                tiene_copago:
                    tieneCopago,

                importe_copago:
                    importeCopago

            });


            // =====================================
            // DEBUG TEMPORAL
            // =====================================

            console.log(
                "Prestación agregada:",
                {
                    codigo: partes[0],
                    origen: origen,
                    importe: importe,

                    tiene_coseguro:
                        tieneCoseguro,

                    importe_coseguro:
                        importeCoseguro,

                    tiene_copago:
                        tieneCopago,

                    importe_copago:
                        importeCopago
                }
            );


            mostrarExito(
                "Prestación agregada correctamente."
            );


            renderPrestaciones();


            // ===============================
            // LIMPIAR CONTROLES
            // ===============================

            selectPrestacion.selectedIndex = 0;

            inputImporte.value = "";

            btnAgregarPrestacion.disabled = true;

            selectPrestacion.focus();

        }
    );


    // =====================================
    // ELIMINAR
    // =====================================

    window.eliminarPrestacion =
        function(index){

            prestaciones.splice(
                index,
                1
            );


            mostrarAdvertencia(
                "Prestación eliminada."
            );


            renderPrestaciones();

        };

}


// ======================================================
// RENDER PRESTACIONES
// ======================================================

function renderPrestaciones(){

    tablaPrestaciones.innerHTML = "";


    prestaciones.forEach(
        function(item,index){

            tablaPrestaciones.innerHTML += `

                <tr>

                    <td>
                        ${item.codigo}
                    </td>

                    <td>
                        ${item.descripcion}
                    </td>

                    <td class="text-center">
                        ${item.cantidad}
                    </td>

                    <td class="text-end">

                        $ ${formatoMoneda(
                            item.cantidad *
                            item.importe
                        )}

                    </td>

                    <td class="text-center">

                        <button
                            type="button"
                            class="btn btn-danger btn-sm"
                            onclick="eliminarPrestacion(${index})">

                            ×

                        </button>

                    </td>

                </tr>

            `;

        }
    );


    // =====================================
    // ACTUALIZAR JSON
    // =====================================

    detallesJson.value =
        JSON.stringify(
            prestaciones
        );


    // =====================================
    // ACTUALIZAR RESUMEN
    // =====================================

    actualizarResumen();

}