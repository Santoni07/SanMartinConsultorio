// ======================================================
// AJAX PRESTACIONES
// ======================================================

function inicializarPrestacionesAjax(){

    const tipo =
        document.getElementById("tipo_concepto");

    const prestacion =
        document.getElementById("id_concepto_facturacion");

    const turno =
        document.getElementById("id_turno");

    const importe =
        document.getElementById("id_importe_particular");


    if(
        !tipo ||
        !prestacion ||
        !turno ||
        !importe
    ){
        return;
    }


    tipo.addEventListener("change", function(){

        // ==========================================
        // LIMPIAR PRESTACIÓN E IMPORTE
        // ==========================================

        prestacion.innerHTML =
            '<option value="">---------</option>';

        importe.value = "";

        if(!this.value){
            return;
        }


        // ==========================================
        // VALIDAR TURNO
        // ==========================================

        if(!turno.value){

            mostrarError(
                "Debe seleccionar un turno antes de elegir el tipo de concepto."
            );

            tipo.value = "";

            return;
        }


        // ==========================================
        // CONSULTAR PRESTACIONES
        // ==========================================

        const url =
            "/caja/ajax/prestaciones/?" +
            "tipo=" +
            encodeURIComponent(this.value) +
            "&turno_id=" +
            encodeURIComponent(turno.value);


        fetch(url)

        .then(async response => {

            const data = await response.json();

            if(!response.ok){

                throw new Error(
                    data.error ||
                    "No se pudieron obtener las prestaciones."
                );

            }

            return data;

        })

        .then(data => {

            if(data.length === 0){

                mostrarAdvertencia(
                    "No existen prestaciones disponibles para esta cobertura y tipo de concepto."
                );

                return;
            }


            data.forEach(function(item){

                const option =
                    document.createElement("option");

                option.value = item.id;

                option.textContent = item.nombre;

                // Guardamos de dónde viene la prestación:
                // PARTICULAR u OBRA_SOCIAL

                option.dataset.origen =
                    item.origen;

                prestacion.appendChild(option);

            });

        })

        .catch(error => {

            console.error(
                "Error cargando prestaciones:",
                error
            );

            mostrarError(error.message);

        });

    });

}


// ======================================================
// AJAX IMPORTE PRESTACIÓN
// ======================================================

function inicializarImporteAjax(){

    const prestacion =
        document.getElementById("id_concepto_facturacion");

    const importe =
        document.getElementById("id_importe_particular");

    const turno =
        document.getElementById("id_turno");


    if(
        !prestacion ||
        !importe ||
        !turno
    ){
        return;
    }


    prestacion.addEventListener("change", function(){

        importe.value = "";


        if(!this.value){
            return;
        }


        if(!turno.value){

            mostrarError(
                "Debe seleccionar un turno."
            );

            return;
        }


        // ==========================================
        // OBTENER ORIGEN DE LA PRESTACIÓN
        // ==========================================

        const opcionSeleccionada =
            this.options[this.selectedIndex];

        const origen =
            opcionSeleccionada.dataset.origen;


        if(!origen){

            mostrarError(
                "No se pudo determinar el origen de la prestación."
            );

            return;
        }


        // ==========================================
        // CONSULTAR IMPORTE
        // ==========================================

        const url =
            "/caja/ajax/importe-prestacion/?" +
            "prestacion_id=" +
            encodeURIComponent(this.value) +
            "&origen=" +
            encodeURIComponent(origen) +
            "&turno_id=" +
            encodeURIComponent(turno.value);


        fetch(url)

        .then(async response => {

            const data = await response.json();

            if(!response.ok){

                throw new Error(
                    data.error ||
                    "No se pudo obtener el importe."
                );

            }

            return data;

        })

        .then(data => {

            importe.value =
                parseFloat(data.importe || 0).toFixed(2);

        })

        .catch(error => {

            console.error(
                "Error obteniendo importe:",
                error
            );

            importe.value = "";

            mostrarError(error.message);

        });

    });

}