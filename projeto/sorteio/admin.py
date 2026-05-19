from django.contrib import admin
from .models import Magistrado, Processo, Assessor, AssistenteJuridico

@admin.register(Magistrado)
class MagistradoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user', 'ativo')

@admin.register(Assessor)
class AssessorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user', 'magistrado')

@admin.register(AssistenteJuridico)
class AssistenteJuridicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'user')

@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'complexidade', 'magistrado', 'status', 'data_cadastro')
    list_filter = ('complexidade', 'status', 'magistrado')
    search_fields = ('numero',)
