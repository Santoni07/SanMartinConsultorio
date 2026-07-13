
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

        mostrarError(
            "Debe seleccionar una prestación."
        );

        return;

    }

    const importe = parseFloat(
        inputImporte.value || 0
    );

    if(importe <= 0){

        mostrarError(
            "El importe de la prestación debe ser mayor a cero."
        );

        return;

    }

    const existente = prestaciones.find(
        p => p.id == selectPrestacion.value
    );

    if(existente){

        existente.cantidad++;
        mostrarAdvertencia(
    "La prestación ya estaba agregada. Se incrementó la cantidad."
);

        renderPrestaciones();

        // ===============================
        // LIMPIAR CONTROLES
        // ===============================

        selectPrestacion.selectedIndex = 0;

        inputImporte.value = "";

        btnAgregarPrestacion.disabled = true;

        selectPrestacion.focus();

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

        importe: importe

    });
    mostrarExito(
    "Prestación agregada correctamente."
);
    renderPrestaciones();

    // ===============================
    // LIMPIAR CONTROLES
    // ===============================

    selectPrestacion.selectedIndex = 0;

    inputImporte.value = "";

    btnAgregarPrestacion.disabled = true;

    selectPrestacion.focus();

});

    // =====================================
    // ELIMINAR
    // =====================================

    window.eliminarPrestacion = function(index){

        prestaciones.splice(index,1);

        mostrarAdvertencia(
            "Prestación eliminada."
        );

        renderPrestaciones();

    };

}

// ======================================================
// RENDER PRESTACIONES
// ======================================================

function renderPrestaciones(){

    tablaPrestaciones.innerHTML = "";

    

    prestaciones.forEach(function(item,index){

      

        tablaPrestaciones.innerHTML += `

            <tr>

                <td>${item.codigo}</td>

                <td>${item.descripcion}</td>

                <td class="text-center">

                    ${item.cantidad}

                </td>

                <td class="text-end">

                   $ ${formatoMoneda(item.cantidad * item.importe)}

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

    

    detallesJson.value =
        JSON.stringify(prestaciones);

    actualizarResumen();

}