
// ======================================================
// FORMULARIO
// ======================================================

function inicializarFormulario(){

    formularioRegistrarCobro =
        document.getElementById(
            "form_registrar_cobro"
        );

    if(!formularioRegistrarCobro){
        return;
    }

    formularioRegistrarCobro.addEventListener(
        "submit",
        function(e){

            if(!validarFormulario()){

                e.preventDefault();

            }

        }
    );

}

// ======================================================
// MENSAJES
// ======================================================

function mostrarError(mensaje){

    mostrarMensaje(
        mensaje,
        "danger"
    );

}

function mostrarExito(mensaje){

    mostrarMensaje(
        mensaje,
        "success"
    );

}

function mostrarAdvertencia(mensaje){

    mostrarMensaje(
        mensaje,
        "warning"
    );

}



function mostrarMensaje(mensaje, tipo){

    const contenedor =
        document.getElementById("mensajes");

    if(!contenedor){
        return;
    }

    const alerta = `

        <div class="alert alert-${tipo} alert-dismissible fade show mb-2">

            ${mensaje}

            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="alert">
            </button>

        </div>

    `;

    contenedor.insertAdjacentHTML(
        "beforeend",
        alerta
    );

    const ultimaAlerta =
        contenedor.lastElementChild;

    setTimeout(function(){

        if(
            ultimaAlerta &&
            document.body.contains(ultimaAlerta)
        ){

            bootstrap.Alert
                .getOrCreateInstance(
                    ultimaAlerta
                )
                .close();

        }

    }, 2000);

}