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