/*
=========================================================
 Centro Médico San Martín
 Módulo: Registrar Movimiento
=========================================================
*/

document.addEventListener("DOMContentLoaded", () => {

    inicializar();

});

// ======================================================
// VARIABLES
// ======================================================

let mediosPago = [];

// ======================================================
// ELEMENTOS
// ======================================================

let btnAgregarMedioPago;

let selectMedioPago;

let inputImporte;

let tablaMediosPago;

let totalMediosPago;

let mediosPagoJson;

// ======================================================
// INICIALIZACIÓN
// ======================================================

function inicializar(){

    inicializarMediosPago();

    inicializarFormulario();
    inicializarExtraCoseguro();

}

// ======================================================
// MEDIOS DE PAGO
// ======================================================

function inicializarMediosPago(){

    btnAgregarMedioPago =
        document.getElementById(
            "btn_agregar_medio_pago"
        );

    selectMedioPago =
        document.getElementById(
            "id_medio_pago"
        );

    inputImporte =
        document.getElementById(
            "importe_medio_pago"
        );

    tablaMediosPago =
        document.querySelector(
            "#tabla_medios_pago tbody"
        );

    totalMediosPago =
        document.getElementById(
            "total_medios_pago"
        );

    mediosPagoJson =
        document.getElementById(
            "medios_pago_json"
        );

    if(
        !btnAgregarMedioPago ||
        !selectMedioPago ||
        !inputImporte ||
        !tablaMediosPago ||
        !totalMediosPago ||
        !mediosPagoJson
    ){
        return;
    }

    btnAgregarMedioPago.addEventListener(
        "click",
        agregarMedioPago
    );

}

// ======================================================
// AGREGAR MEDIO
// ======================================================

function agregarMedioPago(){

    if(
        !selectMedioPago.value ||
        !inputImporte.value
    ){
        return;
    }

    mediosPago.push({

        medio: selectMedioPago.value,

        descripcion:
            selectMedioPago.options[
                selectMedioPago.selectedIndex
            ].text,

        importe: parseFloat(
            inputImporte.value
        )

    });

    renderMediosPago();

    bootstrap.Modal
        .getInstance(
            document.getElementById(
                "modalMedioPago"
            )
        )
        .hide();

    selectMedioPago.value = "";

    inputImporte.value = "";

}

// ======================================================
// RENDER
// ======================================================

function renderMediosPago(){

    tablaMediosPago.innerHTML = "";

    let total = 0;

    mediosPago.forEach(function(item,index){

        total += item.importe;

        tablaMediosPago.innerHTML += `

        <tr>

            <td>${item.descripcion}</td>

            <td class="text-end">

                $ ${item.importe.toFixed(2)}

            </td>

            <td class="text-center">

                <button
                    type="button"
                    class="btn btn-danger btn-sm"
                    onclick="eliminarMedio(${index})">

                    ×

                </button>

            </td>

        </tr>

        `;

    });

    totalMediosPago.innerHTML =
        "$ " + total.toFixed(2);

    mediosPagoJson.value =
        JSON.stringify(
            mediosPago
        );

}

// ======================================================
// ELIMINAR
// ======================================================

window.eliminarMedio = function(index){

    mediosPago.splice(index,1);

    renderMediosPago();

}

// ======================================================
// FORMULARIO
// ======================================================

function inicializarFormulario(){

    const form =
    document.querySelector("form");

    if(!form){
        return;
    }

    form.addEventListener(
        "submit",
        function(e){

            if(
                mediosPago.length === 0
            ){

                alert(
                    "Debe agregar al menos un medio de pago."
                );

                e.preventDefault();

            }

        }
    );

}

// ======================================================
// EXTRA COSEGURO
// ======================================================

function inicializarExtraCoseguro(){

    const selectTipo =
        document.getElementById("id_tipo");

    const selectConcepto =
        document.getElementById(
            "id_concepto_facturacion"
        );

    const bloqueIngreso =
        document.getElementById(
            "bloque_extra_ingreso"
        );

    const bloqueEgreso =
        document.getElementById(
            "bloque_extra_egreso"
        );

    const selectIngreso =
        document.getElementById(
            "id_detalle_extra_ingreso"
        );

    const selectEgreso =
        document.getElementById(
            "id_extra_coseguro_egreso"
        );

    if(
        !selectTipo ||
        !selectConcepto ||
        !bloqueIngreso ||
        !bloqueEgreso ||
        !selectIngreso ||
        !selectEgreso
    ){
        return;
    }

    const actualizarVisibilidad = function(){

        const extraConceptoId =
            selectConcepto.dataset.extraConceptoId;

        const esExtra =
            extraConceptoId &&
            selectConcepto.value === extraConceptoId;

        const esIngreso =
            selectTipo.value === "INGRESO";

        const esEgreso =
            selectTipo.value === "EGRESO";

        bloqueIngreso.classList.toggle(
            "d-none",
            !(esExtra && esIngreso)
        );

        bloqueEgreso.classList.toggle(
            "d-none",
            !(esExtra && esEgreso)
        );

        selectIngreso.required =
            esExtra && esIngreso;

        selectEgreso.required =
            esExtra && esEgreso;

        if(!(esExtra && esIngreso)){
            selectIngreso.value = "";
        }

        if(!(esExtra && esEgreso)){
            selectEgreso.value = "";
        }

    };

    selectTipo.addEventListener(
        "change",
        actualizarVisibilidad
    );

    selectConcepto.addEventListener(
        "change",
        actualizarVisibilidad
    );

    actualizarVisibilidad();

}