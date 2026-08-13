// ======================================================
// COBERTURA DEL PACIENTE
// ======================================================

function inicializarCobertura(){

    const turno =
        document.getElementById("id_turno");

    const contenedor =
        document.getElementById("contenedor_cobertura");

    const paciente =
        document.getElementById("cobertura_paciente");

    const obraSocial =
        document.getElementById("cobertura_obra_social");

    const plan =
        document.getElementById("cobertura_plan");

    const tipoCobertura =
        document.getElementById("tipo_cobertura");


    if(
        !turno ||
        !contenedor ||
        !paciente ||
        !obraSocial ||
        !plan ||
        !tipoCobertura
    ){
        return;
    }


    turno.addEventListener("change", function(){

        // =====================================
        // LIMPIAR COBERTURA
        // =====================================

        contenedor.classList.add("d-none");

        paciente.textContent = "-";
        obraSocial.textContent = "-";
        plan.textContent = "-";

        tipoCobertura.value = "";


        if(!this.value){
            return;
        }


        // =====================================
        // CONSULTAR COBERTURA
        // =====================================

        fetch(
            "/caja/ajax/cobertura-turno/?turno_id=" +
            encodeURIComponent(this.value)
        )

        .then(response => response.json())

        .then(data => {

            if(!data.ok){

                mostrarError(
                    data.error ||
                    "No se pudo obtener la cobertura del paciente."
                );

                return;
            }


            // =====================================
            // MOSTRAR INFORMACIÓN
            // =====================================

            paciente.textContent =
                data.paciente.nombre;

            obraSocial.textContent =
                data.obra_social.nombre;

            tipoCobertura.value =
                data.tipo;


            if(data.plan){

                plan.textContent =
                    data.plan.codigo +
                    " - " +
                    data.plan.nombre;

            }
            else{

                plan.textContent =
                    "Sin plan";

            }


            contenedor.classList.remove("d-none");

        })

        .catch(error => {

            console.error(
                "Error obteniendo cobertura:",
                error
            );

            mostrarError(
                "Ocurrió un error al consultar la cobertura del paciente."
            );

        });

    });

}