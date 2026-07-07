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
    inicializarPrestaciones();

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

    console.log("Inicializando importe");

    const prestacion = document.getElementById(
        "id_concepto_facturacion"
    );

    console.log("Select prestación:", prestacion);

    const importe = document.getElementById(
        "id_importe_particular"
    );

    console.log("Input importe:", importe);

    if(!prestacion || !importe){
        console.log("No encontré los controles");
        return;
    }

    prestacion.addEventListener("change", function(){

        console.log("CHANGE", this.value);

        if(!this.value){
            importe.value = "";
            return;
        }

        fetch(
            "/caja/ajax/importe-prestacion/?concepto_id=" + this.value
        )
        .then(response => response.json())
        .then(data => {
            console.log(data);
            importe.value = data.importe;
        });

    });

}

// ======================================================
// PRESTACIONES
// ======================================================

function inicializarPrestaciones(){

    const btnAgregar = document.getElementById(
        "btn_agregar_prestacion"
    );

    const prestacion = document.getElementById(
        "id_concepto_facturacion"
    );

    const importe = document.getElementById(
        "id_importe_particular"
    );

    const tabla = document.querySelector(
        "#tabla_prestaciones tbody"
    );

    const total = document.getElementById(
        "total_general"
    );

    if(
        !btnAgregar ||
        !prestacion ||
        !importe ||
        !tabla ||
        !total
    ){
        return;
    }

     prestacion.addEventListener("change", function(){

        btnAgregar.disabled = !this.value;

    });


}