from django.contrib import admin
from django.db.models.functions import ExtractYear, ExtractMonth
from django.utils.translation import gettext_lazy as _

from agendas.models import Agendas

class YearFilter(admin.SimpleListFilter):
    title = _('año')
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        years = Agendas.objects.annotate(year=ExtractYear('dia')).order_by('year').values_list('year', flat=True).distinct()
        return [(year, year) for year in years]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(dia__year=self.value())

class MonthFilter(admin.SimpleListFilter):
    title = _('mes')
    parameter_name = 'month'

    def lookups(self, request, model_admin):
        months = Agendas.objects.annotate(month=ExtractMonth('dia')).order_by('month').values_list('month', flat=True).distinct()
        return [(month, month) for month in months]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(dia__month=self.value())

class AgendasAdmin(admin.ModelAdmin):
    list_display = ('dia', 'horario', 'medico')  # Campos que se mostrarán en la lista de objetos
    list_filter = ('dia',  'medico', YearFilter, MonthFilter)    # Filtros que se mostrarán en el panel de administración
    search_fields = ('dia', 'horario', 'medico__nombre')  # Campos por los que se puede buscar
    ordering = ('dia',)  # Ordenar objetos por día


admin.site.register(Agendas, AgendasAdmin)