/*
=========================================================
 Modal Confirmación Global
=========================================================
*/

function abrirModalConfirmacion(

    titulo,

    mensaje,

    url,

    color,

    icono,

    boton,

    detalles = [],

    metodo = "GET"

){

    // ==========================================
    // TÍTULO
    // ==========================================

    document.querySelector(
        "#modalConfirmacion .modal-title"
    ).innerHTML =

        `<i class="bi ${icono}"></i> ${titulo}`;

    // ==========================================
    // COLOR HEADER
    // ==========================================

    document.querySelector(
        "#modalConfirmacion .modal-header"
    ).className =

        `modal-header bg-${color} text-white`;

    // ==========================================
    // MENSAJE
    // ==========================================

    document.querySelector(
        "#modalConfirmacion .modal-body p"
    ).innerHTML = mensaje;

    // ==========================================
    // TABLA DETALLES
    // ==========================================

    const tabla = document.querySelector(
        "#modalConfirmacion table"
    );

    const tbody = document.querySelector(
        "#modalConfirmacion tbody"
    );

    if(tabla){

        tabla.style.display =
            detalles.length ? "" : "none";

    }

    if(tbody){

        tbody.innerHTML = "";

        detalles.forEach(function(item){

            tbody.innerHTML += `

                <tr>

                    <th>${item[0]}</th>

                    <td>${item[1]}</td>

                </tr>

            `;

        });

    }

    // ==========================================
    // BOTÓN CONFIRMAR
    // ==========================================

    const botonConfirmar =
        document.getElementById(
            "btnConfirmarAccion"
        );

    botonConfirmar.dataset.url = url;

    botonConfirmar.dataset.metodo = metodo;

    botonConfirmar.className =
        `btn btn-${color}`;

    botonConfirmar.innerHTML =
        `<i class="bi ${icono}"></i> ${boton}`;

    // ==========================================
    // ABRIR MODAL
    // ==========================================

    const modal =
        new bootstrap.Modal(

            document.getElementById(
                "modalConfirmacion"
            )

        );

    modal.show();

}

/*
=========================================================
 ACCIÓN DEL BOTÓN CONFIRMAR
=========================================================
*/

document.addEventListener(
    "DOMContentLoaded",
    function(){

        const boton =
            document.getElementById(
                "btnConfirmarAccion"
            );

        if(!boton){

            return;

        }

        boton.addEventListener(
            "click",
            function(){

                const url =
                    this.dataset.url;

                const metodo =
                    this.dataset.metodo;

                switch(metodo){

                    case "GET":

                        window.location.href =
                            url;

                        break;

                    case "POST":

                        console.warn(
                            "POST todavía no implementado."
                        );

                        break;

                    case "AJAX":

                        console.warn(
                            "AJAX todavía no implementado."
                        );

                        break;

                    default:

                        console.warn(
                            "Método no soportado:",
                            metodo
                        );

                }

            }
        );

    }
);