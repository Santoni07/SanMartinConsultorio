/*
=========================================================
 Centro Médico San Martín
 Control de inactividad de sesión
=========================================================
*/

document.addEventListener("DOMContentLoaded", () => {

    iniciarControlSesion();

});


// =========================================================
// CONFIGURACIÓN
// =========================================================

const TIEMPO_INACTIVIDAD = 20 * 60 * 1000;   // 20 minutos
const TIEMPO_AVISO = 19 * 60 * 1000;         // Aviso al minuto 19
const CUENTA_REGRESIVA = 60;


// =========================================================
// VARIABLES
// =========================================================

let temporizadorAviso = null;
let temporizadorFin = null;
let temporizadorContador = null;

let segundosRestantes = CUENTA_REGRESIVA;

let modalSesion = null;


// =========================================================
// INICIALIZACIÓN
// =========================================================

function iniciarControlSesion() {

    const modal = document.getElementById("modalSesion");

    if (modal) {

        modalSesion = new bootstrap.Modal(modal);

    }

    registrarEventosUsuario();

    reiniciarTemporizadores();


    const boton = document.getElementById(
        "btnContinuarSesion"
    );

    if (boton) {

        boton.addEventListener(
            "click",
            continuarSesion
        );

    }

}


// =========================================================
// EVENTOS DEL USUARIO
// =========================================================

function registrarEventosUsuario() {

    const eventos = [

        "mousemove",
        "mousedown",
        "keypress",
        "scroll",
        "touchstart",
        "click"

    ];

    eventos.forEach(evento => {

        document.addEventListener(
            evento,
            actividadUsuario,
            true
        );

    });

}


// =========================================================
// ACTIVIDAD DEL USUARIO
// =========================================================

function actividadUsuario() {

    if (modalSesion) {

        const modal = document.getElementById(
            "modalSesion"
        );

        if (
            modal &&
            modal.classList.contains("show")
        ) {

            return;

        }

    }

    reiniciarTemporizadores();

}


// =========================================================
// REINICIAR TEMPORIZADORES
// =========================================================

function reiniciarTemporizadores() {

    clearTimeout(
        temporizadorAviso
    );

    clearTimeout(
        temporizadorFin
    );

    clearInterval(
        temporizadorContador
    );


    segundosRestantes =
        CUENTA_REGRESIVA;


    temporizadorAviso =
        setTimeout(

            mostrarAviso,

            TIEMPO_AVISO

        );


    temporizadorFin =
        setTimeout(

            sesionInactiva,

            TIEMPO_INACTIVIDAD

        );

}


// =========================================================
// MOSTRAR AVISO
// =========================================================

function mostrarAviso() {

    if (!modalSesion) {

        return;

    }

    segundosRestantes =
        CUENTA_REGRESIVA;

    actualizarContador();

    modalSesion.show();


    temporizadorContador =
        setInterval(() => {

            segundosRestantes--;

            actualizarContador();


            if (
                segundosRestantes <= 0
            ) {

                clearInterval(
                    temporizadorContador
                );

            }

        }, 1000);

}


// =========================================================
// ACTUALIZAR CONTADOR
// =========================================================

function actualizarContador() {

    const contador =
        document.getElementById(
            "contadorSesion"
        );

    if (contador) {

        contador.textContent =
            segundosRestantes;

    }

}


// =========================================================
// CONTINUAR SESIÓN
// =========================================================

function continuarSesion() {

    fetch(
        "/renovar-sesion/",
        {
            method: "GET",
            credentials: "same-origin"
        }
    )

    .then(response => {

        if (!response.ok) {

            throw new Error(
                "No se pudo renovar la sesión."
            );

        }

        clearInterval(
            temporizadorContador
        );

        segundosRestantes =
            CUENTA_REGRESIVA;


        if (modalSesion) {

            modalSesion.hide();

        }


        reiniciarTemporizadores();

    })

    .catch(() => {

        window.location.href =
            "/accounts/login/";

    });

}


// =========================================================
// SESIÓN INACTIVA
// =========================================================

function sesionInactiva() {

    clearInterval(
        temporizadorContador
    );

    /*
    IMPORTANTE:

    NO llamamos /accounts/logout/

    Una pestaña vieja podría cerrar la sesión
    mientras el usuario está trabajando en
    otra pestaña.

    Simplemente enviamos esta pestaña al login.
    */

    window.location.href =
        "/accounts/login/";

}