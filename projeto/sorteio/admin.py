from django.contrib import admin
from .models import Juiz, Processo, Assessor, AssistenteJuridico

@admin.register(Juiz)
class JuizAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user', 'ativo')

@admin.register(Assessor)
class AssessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user', 'juiz')

@admin.register(AssistenteJuridico)
class AssistenteJuridicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user')

@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'complexidade', 'juiz', 'status', 'data_cadastro')
    list_filter = ('complexidade', 'status', 'juiz')
    search_fields = ('numero',)
