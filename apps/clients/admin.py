from django.contrib import admin
from .models import Client, CostCenter


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "cliente", "jefatura", "estado")
    list_filter = ("estado", "cliente")
    search_fields = ("nombre", "codigo")
    list_select_related = ("cliente", "jefatura")
