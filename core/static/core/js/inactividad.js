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



const TIEMPO_INACTIVIDAD = 20 * 60 * 1000;     // 20 minutos
const TIEMPO_AVISO = 19 * 60 * 1000;           // Mostrar aviso al minuto 19
const CUENTA_REGRESIVA = 60;                   // 60 segundos

// =========================================================
// VARIABLES
// =========================================================

let temporizadorAviso = null;
let temporizadorLogout = null;
let temporizadorContador = null;

let segundosRestantes = CUENTA_REGRESIVA;

let modalSesion = null;

// =========================================================
// INICIALIZACIÓN
// =========================================================

function iniciarControlSesion(){

    const modal = document.getElementById("modalSesion");

    if(modal){

        modalSesion = new bootstrap.Modal(modal);

    }

    registrarEventosUsuario();

    reiniciarTemporizadores();

    const boton = document.getElementById(
        "btnContinuarSesion"
    );

    if(boton){

        boton.addEventListener(
            "click",
            continuarSesion
        );

    }

}

// =========================================================
// EVENTOS DEL USUARIO
// =========================================================

function registrarEventosUsuario(){

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

function actividadUsuario(){

    if(modalSesion){

        const modalVisible = document
            .getElementById("modalSesion")
            .classList.contains("show");

        if(modalVisible){

            return;

        }

    }

    reiniciarTemporizadores();

}

// =========================================================
// TEMPORIZADORES
// =========================================================

function reiniciarTemporizadores(){

    clearTimeout(temporizadorAviso);
    clearTimeout(temporizadorLogout);
    clearInterval(temporizadorContador);

    segundosRestantes = CUENTA_REGRESIVA;

    temporizadorAviso = setTimeout(

        mostrarAviso,

        TIEMPO_AVISO

    );

    temporizadorLogout = setTimeout(

        cerrarSesion,

        TIEMPO_INACTIVIDAD

    );

}

function mostrarAviso(){

    actualizarContador();

    modalSesion.show();

    temporizadorContador = setInterval(() => {

        segundosRestantes--;

        actualizarContador();

        if(segundosRestantes <= 0){

            clearInterval(
                temporizadorContador
            );

        }

    },1000);

}

// =========================================================
// CONTADOR
// =========================================================

function actualizarContador(){

    const contador = document.getElementById(
        "contadorSesion"
    );

    if(contador){

        contador.textContent = segundosRestantes;

    }

}

// =========================================================
// CONTINUAR SESIÓN
// =========================================================

function continuarSesion(){

    fetch("/renovar-sesion/", {

        method: "GET",

        credentials: "same-origin"

    })
    .then(() => {

        clearInterval(temporizadorContador);

        segundosRestantes = CUENTA_REGRESIVA;

        modalSesion.hide();

        reiniciarTemporizadores();

    })
    .catch(() => {

        window.location.href = "/logout/";

    });

}

// =========================================================
// LOGOUT
// =========================================================

function cerrarSesion(){

    window.location.href = "/accounts/logout/";

}