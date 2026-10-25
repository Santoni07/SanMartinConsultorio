
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

function inicializar() {

    inicializarMediosPago();

    inicializarFormulario();

    // Funcionalidad original de main
    inicializarDepilacion();

    // Funcionalidad de obrasocial
    inicializarExtraCoseguro();

}


// ======================================================
// MEDIOS DE PAGO
// ======================================================

function inicializarMediosPago() {

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

    if (
        !btnAgregarMedioPago ||
        !selectMedioPago ||
        !inputImporte ||
        !tablaMediosPago ||
        !totalMediosPago ||
        !mediosPagoJson
    ) {
        return;
    }

    btnAgregarMedioPago.addEventListener(
        "click",
        agregarMedioPago
    );

}


// ======================================================
// AGREGAR MEDIO DE PAGO
// ======================================================

function agregarMedioPago() {

    if (
        !selectMedioPago.value ||
        !inputImporte.value
    ) {
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
// RENDERIZAR MEDIOS DE PAGO
// ======================================================

function renderMediosPago() {

    tablaMediosPago.innerHTML = "";

    let total = 0;

    mediosPago.forEach(function (item, index) {

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
// ELIMINAR MEDIO DE PAGO
// ======================================================

window.eliminarMedio = function (index) {

    mediosPago.splice(index, 1);

    renderMediosPago();

};


// ======================================================
// FORMULARIO
// ======================================================

function inicializarFormulario() {

    const form =
        document.querySelector("form");

    if (!form) {
        return;
    }

    form.addEventListener(
        "submit",
        function (e) {

            if (
                mediosPago.length === 0
            ) {

                alert(
                    "Debe agregar al menos un medio de pago."
                );

                e.preventDefault();

            }

        }
    );

}


// ======================================================
// DEPILACIÓN - FUNCIONALIDAD ORIGINAL DE MAIN
// ======================================================

function inicializarDepilacion() {

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

    if (
        !selectTipoMovimiento ||
        !bloqueDepilacion ||
        !checkDepilacion ||
        !tipoEgresoDepilacion
    ) {
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


// ======================================================
// ACTUALIZAR VISIBILIDAD DE DEPILACIÓN
// ======================================================

function actualizarDepilacion() {

    if (
        selectTipoMovimiento.value === "EGRESO"
    ) {

        bloqueDepilacion.style.display = "block";

    } else {

        bloqueDepilacion.style.display = "none";

        checkDepilacion.checked = false;

        tipoEgresoDepilacion.style.display = "none";

        return;

    }

    if (checkDepilacion.checked) {

        tipoEgresoDepilacion.style.display =
            "block";

    } else {

        tipoEgresoDepilacion.style.display =
            "none";

    }

}


// ======================================================
// EXTRA COSEGURO - FUNCIONALIDAD DE OBRASOCIAL
// ======================================================

function inicializarExtraCoseguro() {

    const selectTipo =
        document.getElementById(
            "id_tipo"
        );

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

    if (
        !selectTipo ||
        !selectConcepto ||
        !bloqueIngreso ||
        !bloqueEgreso ||
        !selectIngreso ||
        !selectEgreso
    ) {
        return;
    }

    const actualizarVisibilidad = function () {

        const extraConceptoId =
            selectConcepto.dataset.extraConceptoId;

        const esExtra =
            extraConceptoId &&
            selectConcepto.value === extraConceptoId;

        const esIngreso =
            selectTipo.value === "INGRESO";

        const esEgreso =
            selectTipo.value === "EGRESO";

        // Mostrar selector de ingreso extra
        bloqueIngreso.classList.toggle(
            "d-none",
            !(esExtra && esIngreso)
        );

        // Mostrar selector de egreso extra
        bloqueEgreso.classList.toggle(
            "d-none",
            !(esExtra && esEgreso)
        );

        // Campos obligatorios según movimiento
        selectIngreso.required =
            Boolean(esExtra && esIngreso);

        selectEgreso.required =
            Boolean(esExtra && esEgreso);

        // Limpiar selector de ingreso si no corresponde
        if (!(esExtra && esIngreso)) {
            selectIngreso.value = "";
        }

        // Limpiar selector de egreso si no corresponde
        if (!(esExtra && esEgreso)) {
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
