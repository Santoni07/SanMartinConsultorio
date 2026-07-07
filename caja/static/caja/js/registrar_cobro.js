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

    const detallesJson = document.getElementById(
        "detalles_json"
    );

    if(
        !btnAgregar ||
        !prestacion ||
        !importe ||
        !tabla ||
        !total ||
        !detallesJson
    ){
        return;
    }

    // =====================================
    // HABILITAR BOTÓN
    // =====================================

    btnAgregar.disabled = true;

    prestacion.addEventListener("change", function(){

        btnAgregar.disabled = (this.value === "");

    });

    // =====================================
    // AGREGAR PRESTACIÓN
    // =====================================

    btnAgregar.addEventListener("click", function(){

        if(!prestacion.value){
            return;
        }

        const existente = prestaciones.find(
            p => p.id == prestacion.value
        );

        if(existente){

            existente.cantidad++;

            renderTabla();

            return;

        }

        const texto =
            prestacion.options[
                prestacion.selectedIndex
            ].text;

        const partes = texto.split(" - ");

        prestaciones.push({

            id: prestacion.value,

            codigo: partes[0],

            descripcion: partes.slice(1).join(" - "),

            cantidad: 1,

            importe: parseFloat(
                importe.value || 0
            )

        });

        renderTabla();

    });

    // =====================================
    // RENDER TABLA
    // =====================================

    function renderTabla(){

        tabla.innerHTML = "";

        let totalGeneral = 0;

        prestaciones.forEach(function(item,index){

            totalGeneral +=
                item.cantidad *
                item.importe;

            tabla.innerHTML += `

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

        total.innerHTML =
            "$ " +
            totalGeneral.toFixed(2);

        detallesJson.value =
            JSON.stringify(prestaciones);

    }

    // =====================================
    // ELIMINAR
    // =====================================

    window.eliminarPrestacion = function(index){

        prestaciones.splice(index,1);

        renderTabla();

    }

}