from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CustomLogoutView.as_view(), name="logout"),
    path(
        "cambiar-contrasena/",
        views.CustomPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "cambiar-contrasena/hecho/",
        views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path(
        "recuperar-contrasena/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "recuperar-contrasena/hecho/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "recuperar/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "recuperar-contrasena/completado/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("perfil/", views.ProfileView.as_view(), name="profile"),
    path("usuarios/", views.UserListView.as_view(), name="user_list"),
    path("usuarios/nuevo/", views.UserCreateView.as_view(), name="user_create"),
    path("usuarios/<int:pk>/editar/", views.UserUpdateView.as_view(), name="user_edit"),
]
