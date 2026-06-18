from django.contrib import admin
from .models import AssetType, Asset, AssetAssignment


class AssetAssignmentInline(admin.TabularInline):
    model = AssetAssignment
    extra = 0
    readonly_fields = (
        "fecha_asignacion",
        "fecha_devolucion",
        "estado_devolucion",
        "trabajador",
    )
    can_delete = False


@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ("nombre", "estado", "es_personalizado")
    list_filter = ("estado", "es_personalizado")
    search_fields = ("nombre",)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "tipo", "estado", "fecha_registro")
    list_filter = ("estado", "tipo")
    search_fields = ("codigo", "nombre")
    list_select_related = ("tipo",)
    inlines = (AssetAssignmentInline,)


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "activo",
        "trabajador",
        "fecha_asignacion",
        "fecha_devolucion",
        "estado_devolucion",
    )
    list_filter = ("estado_devolucion",)
    search_fields = ("activo__codigo", "trabajador__nombre")
    list_select_related = ("activo", "trabajador")
