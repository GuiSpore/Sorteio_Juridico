from django.contrib import admin
from .models import Juiz, Processo

@admin.register(Juiz)
class JuizAdmin(admin.ModelAdmin):
    list_display = ('nome',)

@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'complexidade', 'juiz', 'data_cadastro')
    list_filter = ('complexidade', 'juiz')
    search_fields = ('numero',)
