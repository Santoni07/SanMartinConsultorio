from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import NomencladorGeneral
from .forms import NomencladorGeneralForm


def lista_nomenclador(request):

    nomencladores = NomencladorGeneral.objects.all()

    return render(
        request,
        'nomenclador/lista.html',
        {
            'nomencladores': nomencladores
        }
    )


def nuevo_nomenclador(request):

    form = NomencladorGeneralForm(request.POST or None)

    if form.is_valid():

        form.save()

        messages.success(
            request,
            'Prestación creada correctamente.'
        )

        return redirect('lista_nomenclador')

    return render(
        request,
        'nomenclador/form.html',
        {
            'form': form,
            'titulo': 'Nuevo Nomenclador'
        }
    )


def editar_nomenclador(request, pk):

    nomenclador = get_object_or_404(
        NomencladorGeneral,
        pk=pk
    )

    form = NomencladorGeneralForm(
        request.POST or None,
        instance=nomenclador
    )

    if form.is_valid():

        form.save()

        messages.success(
            request,
            'Prestación modificada correctamente.'
        )

        return redirect('lista_nomenclador')

    return render(
        request,
        'nomenclador/form.html',
        {
            'form': form,
            'titulo': 'Editar Nomenclador'
        }
    )


def eliminar_nomenclador(request, pk):

    nomenclador = get_object_or_404(
        NomencladorGeneral,
        pk=pk
    )

    nomenclador.delete()

    messages.success(
        request,
        'Prestación eliminada correctamente.'
    )

    return redirect('lista_nomenclador')