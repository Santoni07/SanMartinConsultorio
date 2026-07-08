/*
=========================================================
 Centro Médico San Martín
 Módulo: Registrar Cobro
=========================================================
*/

document.addEventListener("DOMContentLoaded", () => {

    inicializar();

});

// ======================================================
// VARIABLES GLOBALES
// ======================================================

let prestaciones = [];

let mediosPago = [];

// ======================================================
// DOM - PRESTACIONES
// ======================================================

let btnAgregarPrestacion;

let selectPrestacion;

let inputImporte;

let tablaPrestaciones;

let totalPrestaciones;

let detallesJson;


// ======================================================
// DOM - MEDIOS DE PAGO
// ======================================================

let btnAgregarMedioPago;

let selectMedioPago;

let inputImporteMedioPago;

let tablaMediosPago;

let mediosPagoJson;

let totalMediosPago;

// ======================================================
// DOM - FORMULARIO
// ======================================================

let formularioRegistrarCobro;

// ======================================================
// INICIALIZACIÓN
// ======================================================

function inicializar(){

    inicializarPrestacionesAjax();
    inicializarImporteAjax();
    inicializarPrestaciones();
    inicializarMediosPago();
    inicializarFormulario();

}


