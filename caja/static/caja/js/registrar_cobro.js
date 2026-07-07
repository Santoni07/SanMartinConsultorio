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
// INICIALIZACIÓN
// ======================================================

function inicializar(){

    inicializarPrestacionesAjax();
    inicializarImporteAjax();

}
// ======================================================
// AJAX PRESTACIONES
// ======================================================

function inicializarPrestacionesAjax(){

    const tipo = document.getElementById(
        "tipo_concepto"
    );

    const prestacion = document.getElementById(
        "id_concepto_facturacion"
    );

    if(!tipo || !prestacion){
        return;
    }

    tipo.addEventListener("change", function(){

        prestacion.innerHTML =
            '<option value="">---------</option>';

        document.getElementById(
            "id_importe_particular"
        ).value = "";

        if(!this.value){
            return;
        }

        fetch(
            "/caja/ajax/prestaciones/?tipo=" + this.value
        )

        .then(response => response.json())

        .then(data => {

            data.forEach(function(item){

                let option =
                    document.createElement("option");

                option.value = item.id;

                option.textContent = item.nombre;

                prestacion.appendChild(option);

            });

        });

    });

}

// ======================================================
// AJAX IMPORTE PRESTACIÓN
// ======================================================

function inicializarImporteAjax(){

    const prestacion = document.getElementById(
        "id_concepto_facturacion"
    );

    const importe = document.getElementById(
        "id_importe_particular"
    );

    if(!prestacion || !importe){
        return;
    }

    prestacion.addEventListener("change", function(){
        console.log("Prestación seleccionada:", this.value);
        if(!this.value){

            importe.value = "";

            return;

        }

        fetch(
            "/caja/ajax/importe-prestacion/?concepto_id=" +
            this.value
        )

        .then(response => response.json())

        .then(data => {

            importe.value = data.importe;

        });

    });

}