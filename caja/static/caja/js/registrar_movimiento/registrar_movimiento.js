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
let selectTipoMovimiento;

let bloqueDepilacion;

let checkDepilacion;

let tipoEgresoDepilacion;

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
    inicializarDepilacion();

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
// DEPILACIÓN
// ======================================================

function inicializarDepilacion(){

    selectTipoMovimiento =
        document.getElementById(
            "id_tipo"
        );

    bloqueDepilacion =
        document.getElementById(
            "bloque_depilacion"
        );

    checkDepilacion =
        document.getElementById(
            "id_es_depilacion"
        );

    tipoEgresoDepilacion =
        document.getElementById(
            "tipo_egreso_depilacion"
        );

    if(
        !selectTipoMovimiento ||
        !bloqueDepilacion ||
        !checkDepilacion ||
        !tipoEgresoDepilacion
    ){
        return;
    }

    selectTipoMovimiento.addEventListener(
        "change",
        actualizarDepilacion
    );

    checkDepilacion.addEventListener(
        "change",
        actualizarDepilacion
    );

    actualizarDepilacion();

}
function actualizarDepilacion(){

    if(
        selectTipoMovimiento.value === "EGRESO"
    ){

        bloqueDepilacion.style.display = "block";

    }else{

        bloqueDepilacion.style.display = "none";

        checkDepilacion.checked = false;

        tipoEgresoDepilacion.style.display = "none";

        return;

    }

    if(checkDepilacion.checked){

        tipoEgresoDepilacion.style.display =
            "block";

    }else{

        tipoEgresoDepilacion.style.display =
            "none";

    }

}