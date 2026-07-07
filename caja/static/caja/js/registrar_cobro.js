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
// ELEMENTOS DEL DOM
// ======================================================

let btnAgregarPrestacion;

let selectPrestacion;

let inputImporte;

let tablaPrestaciones;

let totalPrestaciones;

let detallesJson;

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

    selectPrestacion.addEventListener("change", function(){

        btnAgregarPrestacion.disabled =
            (this.value === "");

    });

    // =====================================
    // AGREGAR PRESTACIÓN
    // =====================================

    btnAgregarPrestacion.addEventListener("click", function(){

        if(!selectPrestacion.value){
            return;
        }

        const existente = prestaciones.find(
            p => p.id == selectPrestacion.value
        );

        if(existente){

            existente.cantidad++;

            renderPrestaciones();

            return;

        }

        const texto =
            selectPrestacion.options[
                selectPrestacion.selectedIndex
            ].text;

        const partes = texto.split(" - ");

        prestaciones.push({

            id: selectPrestacion.value,

            codigo: partes[0],

            descripcion: partes.slice(1).join(" - "),

            cantidad: 1,

            importe: parseFloat(
                inputImporte.value || 0
            )

        });

        renderPrestaciones();

    });

    // =====================================
    // ELIMINAR
    // =====================================

    window.eliminarPrestacion = function(index){

        prestaciones.splice(index,1);

        renderPrestaciones();

    };

}

// ======================================================
// RENDER PRESTACIONES
// ======================================================

function renderPrestaciones(){

    tablaPrestaciones.innerHTML = "";

    let totalGeneral = 0;

    prestaciones.forEach(function(item,index){

        totalGeneral +=
            item.cantidad *
            item.importe;

        tablaPrestaciones.innerHTML += `

            <tr>

                <td>${item.codigo}</td>

                <td>${item.descripcion}</td>

                <td class="text-center">

                    ${item.cantidad}

                </td>

                <td class="text-end">

                    $ ${(item.cantidad * item.importe).toFixed(2)}

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

    });

    totalPrestaciones.innerHTML =
        "$ " +
        totalGeneral.toFixed(2);

    detallesJson.value =
        JSON.stringify(prestaciones);

}