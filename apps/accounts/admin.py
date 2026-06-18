from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role, UserRole


class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "nombre",
        "is_active",
        "contrasena_temporal",
        "date_joined",
    )
    list_filter = ("is_active", "contrasena_temporal")
    search_fields = ("email", "nombre")
    ordering = ("email",)
    inlines = (UserRoleInline,)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información personal", {"fields": ("nombre",)}),
        (
            "Estado",
            {"fields": ("is_active", "contrasena_temporal", "intentos_fallidos")},
        ),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "nombre", "password1", "password2", "is_active"),
            },
        ),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("usuario", "rol", "fecha_asignacion")
    list_filter = ("rol",)
    search_fields = ("usuario__email", "usuario__nombre")
