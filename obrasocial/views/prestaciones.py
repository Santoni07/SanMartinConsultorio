from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404,redirect
from decimal import Decimal, InvalidOperation
from nomenclador.models import NomencladorGeneral
import openpyxl
from django.urls import reverse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from ..models import (
    ObraSocial,
    PrestacionPlan,
    PlanObraSocial
)
from ..forms import PrestacionPlanForm
from django.db.models import Q

@login_required
def listar_prestaciones(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id
    )

    plan = None

    plan_id = request.GET.get("plan")

    prestaciones = (
        PrestacionPlan.objects
        .filter(obra_social=obra_social)
        .select_related(
            "nomenclador",
            "plan",
            "proveedor"
        )
    )

    # =========================================================
    # CON PLAN / SIN PLAN
    # =========================================================

    if plan_id:

        plan = get_object_or_404(
            PlanObraSocial,
            pk=plan_id,
            obra_social=obra_social
        )

        prestaciones = prestaciones.filter(
            plan=plan
        )

    else:

        prestaciones = prestaciones.filter(
            plan__isnull=True
        )

    # =========================================================
    # BUSCADOR
    # =========================================================

    buscar = request.GET.get(
        "buscar",
        ""
    ).strip()

    if buscar:

        prestaciones = prestaciones.filter(
            Q(nomenclador__codigo__icontains=buscar) |
            Q(nomenclador__descripcion__icontains=buscar)
        )

    # =========================================================
    # TOTALES
    # =========================================================

    total = prestaciones.count()

    activas = prestaciones.filter(
        estado="ACTIVA"
    ).count()

    inactivas = prestaciones.filter(
        estado="INACTIVA"
    ).count()

    # =========================================================
    # ORDEN
    # Últimas prestaciones cargadas primero
    # =========================================================

    prestaciones = prestaciones.order_by("-id")

    context = {

        "obra_social": obra_social,

        "plan": plan,

        "prestaciones": prestaciones,

        "buscar": buscar,

        "total": total,

        "activas": activas,

        "inactivas": inactivas,
    }

    return render(
        request,
        "obrasocial/prestaciones/lista.html",
        context
    )
    
@login_required
def importar_excel_prestaciones(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id
    )

    # =====================================================
    # OBTENER PLAN
    # =====================================================

    plan = None

    plan_id = (
        request.GET.get("plan")
        or request.POST.get("plan")
    )

    if plan_id:

        plan = get_object_or_404(
            PlanObraSocial,
            pk=plan_id,
            obra_social=obra_social
        )

    # =====================================================
    # SEGURIDAD
    # Si la obra social usa planes, debe existir un plan
    # seleccionado.
    # =====================================================

    if obra_social.usa_planes and not plan:

        messages.error(
            request,
            "Debe seleccionar un plan para importar las prestaciones."
        )

        return redirect(
            "obrasocial:detail",
            pk=obra_social.id
        )

    # =====================================================
    # POST
    # =====================================================

    if request.method == "POST":

        archivo = request.FILES.get("archivo")

        if not archivo:

            messages.error(
                request,
                "Debe seleccionar un archivo Excel."
            )

            # Conservamos el plan
            if plan:

                return redirect(
                    f"{reverse('obrasocial:importar_excel_prestaciones', kwargs={'obra_social_id': obra_social.id})}?plan={plan.id}"
                )

            return redirect(
                "obrasocial:importar_excel_prestaciones",
                obra_social_id=obra_social.id
            )

        if not archivo.name.lower().endswith(".xlsx"):

            messages.error(
                request,
                "El archivo debe tener formato .xlsx."
            )

            if plan:

                return redirect(
                    f"{reverse('obrasocial:importar_excel_prestaciones', kwargs={'obra_social_id': obra_social.id})}?plan={plan.id}"
                )

            return redirect(
                "obrasocial:importar_excel_prestaciones",
                obra_social_id=obra_social.id
            )

        # =================================================
        # ABRIR EXCEL
        # =================================================

        try:

            workbook = openpyxl.load_workbook(
                archivo,
                data_only=True
            )

            hoja = workbook.active

        except Exception:

            messages.error(
                request,
                "No se pudo leer el archivo Excel."
            )

            if plan:

                return redirect(
                    f"{reverse('obrasocial:importar_excel_prestaciones', kwargs={'obra_social_id': obra_social.id})}?plan={plan.id}"
                )

            return redirect(
                "obrasocial:importar_excel_prestaciones",
                obra_social_id=obra_social.id
            )

        # =================================================
        # CONTADORES
        # =================================================

        creadas = 0
        actualizadas = 0
        importe_cero = 0
        no_encontradas = []

        # =================================================
        # CONVERTIR IMPORTES
        # =================================================

        def convertir_importe(valor):

            if valor is None:
                return Decimal("0.00")

            # Excel ya lo entrega como número
            if isinstance(valor, (int, float, Decimal)):

                try:
                    return Decimal(str(valor))

                except (InvalidOperation, ValueError):
                    return Decimal("0.00")

            texto = str(valor).strip()

            if not texto:
                return Decimal("0.00")

            # Sacamos símbolo de moneda y espacios
            texto = texto.replace("$", "")
            texto = texto.replace(" ", "")

            try:

                # Formato argentino:
                # 47.660,06
                if "," in texto:

                    texto = texto.replace(".", "")
                    texto = texto.replace(",", ".")

                return Decimal(texto)

            except (InvalidOperation, ValueError):

                # Incluye FALTA, textos inválidos, etc.
                return Decimal("0.00")

        # =================================================
        # PROCESAMIENTO
        # =================================================

        try:

            with transaction.atomic():

                for numero_fila, fila in enumerate(
                    hoja.iter_rows(values_only=True),
                    start=1
                ):

                    # Evitamos problemas con filas incompletas
                    if len(fila) < 3:
                        continue

                    codigo = fila[0]
                    descripcion_excel = fila[1]
                    importe_excel = fila[2]

                    # -------------------------------------
                    # NECESITAMOS CÓDIGO + DESCRIPCIÓN
                    # -------------------------------------

                    if codigo is None or descripcion_excel is None:
                        continue

                    codigo = str(codigo).strip()

                    descripcion_excel = str(
                        descripcion_excel
                    ).strip()

                    if not codigo or not descripcion_excel:
                        continue

                    # -------------------------------------
                    # Excel puede entregar 110319.0
                    # -------------------------------------

                    if codigo.endswith(".0"):
                        codigo = codigo[:-2]

                    # -------------------------------------
                    # DESCARTAR TÍTULOS / ENCABEZADOS
                    # -------------------------------------

                    if not codigo.isdigit():
                        continue

                    # -------------------------------------
                    # BUSCAR EN NOMENCLADOR GENERAL
                    # -------------------------------------

                    nomenclador = (
                        NomencladorGeneral.objects
                        .filter(codigo=codigo)
                        .first()
                    )

                    if not nomenclador:

                        no_encontradas.append({
                            "fila": numero_fila,
                            "codigo": codigo,
                            "descripcion": descripcion_excel,
                        })

                        continue

                    # -------------------------------------
                    # CONVERTIR IMPORTE
                    # -------------------------------------

                    valor = convertir_importe(
                        importe_excel
                    )

                    if valor == 0:
                        importe_cero += 1

                    # =====================================
                    # CREAR O ACTUALIZAR PRESTACIÓN
                    #
                    # SIN PLAN:
                    # plan = None
                    #
                    # CON PLAN:
                    # plan = SWM-210, SMG20, etc.
                    # =====================================

                    prestacion, creada = (
                        PrestacionPlan.objects.get_or_create(

                            obra_social=obra_social,

                            plan=plan,

                            nomenclador=nomenclador,

                            defaults={
                                "valor": valor,
                                "fecha_vigencia_desde": timezone.localdate(),
                                "estado": "ACTIVA",
                            }
                        )
                    )

                    if creada:

                        creadas += 1

                    else:

                        prestacion.valor = valor
                        prestacion.estado = "ACTIVA"

                        prestacion.save(
                            update_fields=[
                                "valor",
                                "estado",
                                "fecha_modificacion",
                            ]
                        )

                        actualizadas += 1

        except Exception as error:

            messages.error(
                request,
                f"Ocurrió un error al importar el archivo: {error}"
            )

            if plan:

                return redirect(
                    f"{reverse('obrasocial:importar_excel_prestaciones', kwargs={'obra_social_id': obra_social.id})}?plan={plan.id}"
                )

            return redirect(
                "obrasocial:importar_excel_prestaciones",
                obra_social_id=obra_social.id
            )

        # =================================================
        # GUARDAR RESULTADO EN SESIÓN
        # =================================================

        request.session["resultado_importacion"] = {

            "creadas": creadas,

            "actualizadas": actualizadas,

            "importe_cero": importe_cero,

            "no_encontradas": no_encontradas,

            # Guardamos también de qué plan vino
            "plan_id": plan.id if plan else None,
        }

        # =================================================
        # DEBUG
        # =================================================

        print("====================================")
        print("RESULTADO IMPORTACION")
        print("Obra Social:", obra_social.nombre)

        if plan:
            print("Plan:", plan.codigo)
        else:
            print("Plan: SIN PLAN")

        print("Creadas:", creadas)
        print("Actualizadas:", actualizadas)
        print("Importe cero:", importe_cero)
        print("No encontradas:", len(no_encontradas))
        print(
            "Primeras no encontradas:",
            no_encontradas[:10]
        )
        print("====================================")

        # =================================================
        # MENSAJE
        # =================================================

        messages.success(
            request,
            f"Importación finalizada. "
            f"Nuevas: {creadas} - "
            f"Actualizadas: {actualizadas} - "
            f"Importe $0: {importe_cero} - "
            f"No encontradas: {len(no_encontradas)}."
        )

        # =================================================
        # RESULTADO
        # =================================================

        url_resultado = reverse(
            "obrasocial:resultado_importacion_prestaciones",
            kwargs={
                "obra_social_id": obra_social.id
            }
        )

        if plan:
            url_resultado += f"?plan={plan.id}"

        return redirect(
            url_resultado
        )

    # =====================================================
    # GET
    # =====================================================

    context = {

        "obra_social": obra_social,

        "plan": plan,

    }

    return render(
        request,
        "obrasocial/prestaciones/importar_excel.html",
        context
    )
@login_required
def resultado_importacion_prestaciones(request, obra_social_id):

    obra_social = get_object_or_404(
        ObraSocial,
        pk=obra_social_id
    )

    resultado = request.session.get(
        "resultado_importacion"
    )

    # Si se entra directamente sin haber realizado
    # una importación, volvemos al listado.
    if not resultado:

        messages.warning(
            request,
            "No hay resultados de importación para mostrar."
        )

        return redirect(
            "obrasocial:listar_prestaciones",
            obra_social_id=obra_social.id
        )

    context = {
        "obra_social": obra_social,
        "resultado": resultado,
    }

    return render(
        request,
        "obrasocial/prestaciones/resultado_importacion.html",
        context
    )

@login_required
def crear_prestacion(request, obra_social_id):
    return HttpResponse("Crear Prestación")

@login_required
def editar_prestacion(request, pk):

    prestacion = get_object_or_404(
        PrestacionPlan.objects.select_related(
            "obra_social",
            "plan",
            "nomenclador",
            "proveedor",
        ),
        pk=pk
    )

    obra_social = prestacion.obra_social
    plan = prestacion.plan

    if request.method == "POST":

        form = PrestacionPlanForm(
            request.POST,
            instance=prestacion
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "La prestación fue modificada correctamente."
            )

            # URL base del listado
            url = reverse(
                "obrasocial:listar_prestaciones",
                kwargs={
                    "obra_social_id": obra_social.id
                }
            )

            # Si la prestación pertenece a un plan,
            # volvemos al listado de ESE plan.
            if plan:
                url += f"?plan={plan.id}"

            return redirect(url)

    else:

        form = PrestacionPlanForm(
            instance=prestacion
        )

    context = {
        "obra_social": obra_social,
        "plan": plan,
        "prestacion": prestacion,
        "form": form,
    }

    return render(
        request,
        "obrasocial/prestaciones/editar.html",
        context
    )

   
@login_required
def detalle_prestacion(request, pk):

    prestacion = get_object_or_404(
        PrestacionPlan.objects.select_related(
            "obra_social",
            "plan",
            "nomenclador",
            "proveedor",
        ),
        pk=pk
    )

    context = {
        "obra_social": prestacion.obra_social,
        "prestacion": prestacion,
    }

    return render(
        request,
        "obrasocial/prestaciones/detalle.html",
        context
    )


@login_required
def desactivar_prestacion(request, pk):
    return HttpResponse("Desactivar Prestación")