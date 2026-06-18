from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("inventario/", views.AssetListView.as_view(), name="asset_list"),
    path("inventario/nuevo/", views.AssetCreateView.as_view(), name="asset_create"),
    path("inventario/<int:pk>/", views.AssetDetailView.as_view(), name="asset_detail"),
    path(
        "inventario/<int:pk>/editar/",
        views.AssetUpdateView.as_view(),
        name="asset_edit",
    ),
    path(
        "inventario/<int:pk>/asignar/",
        views.AssetAssignView.as_view(),
        name="asset_assign",
    ),
    path(
        "inventario/<int:pk>/devolver/",
        views.AssetReturnView.as_view(),
        name="asset_return",
    ),
    path("inventario/<int:pk>/baja/", views.AssetBajaView.as_view(), name="asset_baja"),
]
