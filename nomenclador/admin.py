from django.contrib import admin


from .models import NomencladorGeneral


@admin.register(NomencladorGeneral)
class NomencladorGeneralAdmin(admin.ModelAdmin):

    list_display = (
        'codigo',
        'descripcion',
        'activo',
    )

    search_fields = (
        'codigo',
        'descripcion',
    )

    ordering = (
        'codigo',
    )