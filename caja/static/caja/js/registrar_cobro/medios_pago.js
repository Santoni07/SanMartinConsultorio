// ======================================================
// MEDIOS DE PAGO
// ======================================================

function inicializarMediosPago(){

    btnAgregarMedioPago = document.getElementById(
        "btn_agregar_medio_pago"
    );

    selectMedioPago = document.getElementById(
        "id_medio_pago"
    );

    inputImporteMedioPago = document.getElementById(
        "importe_medio_pago"
    );

    tablaMediosPago = document.querySelector(
        "#tabla_medios_pago tbody"
    );

    mediosPagoJson = document.getElementById(
        "medios_pago_json"
    );

    totalMediosPago = document.getElementById(
        "total_medios_pago"
    );

    if(
        !btnAgregarMedioPago ||
        !selectMedioPago ||
        !inputImporteMedioPago ||
        !tablaMediosPago ||
        !mediosPagoJson ||
        !totalMediosPago
    ){
        return;
    }

    // =====================================
    // CUANDO SE ABRE EL MODAL
    // =====================================

    const modal = document.getElementById(
        "modalMedioPago"
    );

    if(modal){

        modal.addEventListener(
            "shown.bs.modal",
            function(){

                const saldo =
                    obtenerSaldoPendiente();

                if(saldo > 0){

                    inputImporteMedioPago.value =
                        saldo.toFixed(2);

                }
                else{

                    inputImporteMedioPago.value = "";

                }

                selectMedioPago.focus();

            }
        );

    }

    btnAgregarMedioPago.disabled = true;

    selectMedioPago.addEventListener("change", function(){

        btnAgregarMedioPago.disabled =
            (this.value === "");

    });

    btnAgregarMedioPago.addEventListener("click", function(){

        if(!selectMedioPago.value){

            mostrarError(
                "Debe seleccionar un medio de pago."
            );

            return;

        }

        if(obtenerTotalPrestaciones() <= 0){

            mostrarError(
                "Debe agregar al menos una prestación antes de registrar medios de pago."
            );

            return;

        }

        const importe = parseFloat(
            inputImporteMedioPago.value || 0
        );

        if(importe <= 0){

            mostrarError(
                "El importe debe ser mayor a cero."
            );

            inputImporteMedioPago.focus();

            return;

        }

        const saldoPendiente =
            obtenerSaldoPendiente();

        if(importe > saldoPendiente){

            mostrarError(

                "El importe supera el saldo pendiente.\n\n" +

                "Saldo pendiente: $" +
                saldoPendiente.toFixed(2) +

                "\n\nExceso: $" +

                (importe - saldoPendiente)
                .toFixed(2)

            );

            inputImporteMedioPago.focus();

            return;

        }

        mediosPago.push({

            medio: selectMedioPago.value,

            descripcion:

                selectMedioPago.options[
                    selectMedioPago.selectedIndex
                ].text,

            importe: importe

        });

        mostrarExito(
            "Medio de pago agregado correctamente."
        );

        renderMediosPago();

        // =====================================
        // LIMPIAR CONTROLES
        // =====================================

        selectMedioPago.selectedIndex = 0;

        const nuevoSaldo =
            obtenerSaldoPendiente();

        if(nuevoSaldo > 0){

            inputImporteMedioPago.value =
                nuevoSaldo.toFixed(2);

        }
        else{

            inputImporteMedioPago.value = "";

        }

        btnAgregarMedioPago.disabled = true;

        selectMedioPago.focus();

    });

    window.eliminarMedioPago = function(index){

        mediosPago.splice(index,1);

        mostrarAdvertencia(
            "Medio de pago eliminado."
        );

        renderMediosPago();

        const saldo =
            obtenerSaldoPendiente();

        if(saldo > 0){

            inputImporteMedioPago.value =
                saldo.toFixed(2);

        }

    };

}

// ======================================================
// RENDER MEDIOS DE PAGO
// ======================================================

function renderMediosPago(){

    tablaMediosPago.innerHTML = "";

    mediosPago.forEach(function(item,index){

        tablaMediosPago.innerHTML += `

            <tr>

                <td>${item.descripcion}</td>

                <td class="text-end">

                    $ ${formatoMoneda(item.importe)}

                </td>

                <td class="text-center">

                    <button
                        type="button"
                        class="btn btn-danger btn-sm"
                        onclick="eliminarMedioPago(${index})">

                        ×

                    </button>

                </td>

            </tr>

        `;

    });

    mediosPagoJson.value =
        JSON.stringify(mediosPago);

    actualizarResumen();

}

// ======================================================
// UTILIDADES
// ======================================================

function obtenerTotalPrestaciones(){

    return prestaciones.reduce(function(total,item){

        return total +
            (item.cantidad * item.importe);

    },0);

}

function obtenerTotalMediosPago(){

    return mediosPago.reduce(function(total,item){

        return total +
            item.importe;

    },0);

}

function obtenerSaldoPendiente(){

    return (

        obtenerTotalPrestaciones() -

        obtenerTotalMediosPago()

    );

}