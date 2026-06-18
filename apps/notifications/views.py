from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, View

from apps.accounts.decorators import RoleRequiredMixin
from .models import Notification


class NotificationListView(RoleRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    roles_requeridos = [
        "administrador",
        "rrhh",
        "ti",
        "finanzas",
        "logistica",
        "prevencion",
        "jefatura",
    ]
    paginate_by = 30

    def get_queryset(self):
        qs = Notification.objects.filter(
            usuario_destinatario=self.request.user,
        ).exclude(estado=Notification.EstadoChoices.ELIMINADA)

        filtro = self.request.GET.get("filtro", "")
        if filtro == "no_leidas":
            qs = qs.filter(estado=Notification.EstadoChoices.ENVIADA)
        elif filtro == "leidas":
            qs = qs.filter(estado=Notification.EstadoChoices.LEIDA)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filtro"] = self.request.GET.get("filtro", "")
        ctx["no_leidas"] = Notification.objects.filter(
            usuario_destinatario=self.request.user,
            estado=Notification.EstadoChoices.ENVIADA,
        ).count()
        return ctx


class NotificationMarkReadView(RoleRequiredMixin, View):
    roles_requeridos = [
        "administrador",
        "rrhh",
        "ti",
        "finanzas",
        "logistica",
        "prevencion",
        "jefatura",
    ]

    def _get_redirect_url(self, notif):
        if notif.tarea:
            return reverse("kanban:card_detail", kwargs={"pk": notif.tarea.pk})
        if notif.proceso:
            return reverse("processes:process_detail", kwargs={"pk": notif.proceso.pk})
        return reverse("notifications:list")

    def post(self, request, pk):
        notif = get_object_or_404(
            Notification, pk=pk, usuario_destinatario=request.user
        )
        notif.estado = Notification.EstadoChoices.LEIDA
        notif.save(update_fields=["estado"])
        return redirect(self._get_redirect_url(notif))

    def get(self, request, pk):
        notif = get_object_or_404(
            Notification, pk=pk, usuario_destinatario=request.user
        )
        notif.estado = Notification.EstadoChoices.LEIDA
        notif.save(update_fields=["estado"])
        return redirect(self._get_redirect_url(notif))


class NotificationMarkAllReadView(RoleRequiredMixin, View):
    roles_requeridos = [
        "administrador",
        "rrhh",
        "ti",
        "finanzas",
        "logistica",
        "prevencion",
        "jefatura",
    ]

    def post(self, request):
        Notification.objects.filter(
            usuario_destinatario=request.user,
            estado=Notification.EstadoChoices.ENVIADA,
        ).update(estado=Notification.EstadoChoices.LEIDA)
        messages.success(request, "Todas las notificaciones marcadas como leídas.")
        next_url = request.GET.get("next") or request.POST.get("next", "")
        if next_url:
            return redirect(next_url)
        return redirect("notifications:list")


class NotificationDeleteView(RoleRequiredMixin, View):
    roles_requeridos = [
        "administrador",
        "rrhh",
        "ti",
        "finanzas",
        "logistica",
        "prevencion",
        "jefatura",
    ]

    def post(self, request, pk):
        notif = get_object_or_404(
            Notification, pk=pk, usuario_destinatario=request.user
        )
        notif.estado = Notification.EstadoChoices.ELIMINADA
        notif.save(update_fields=["estado"])
        next_url = request.GET.get("next") or request.POST.get("next", "")
        if next_url:
            return redirect(next_url)
        return redirect("notifications:list")


class NotificationCountView(RoleRequiredMixin, View):
    roles_requeridos = [
        "administrador",
        "rrhh",
        "ti",
        "finanzas",
        "logistica",
        "prevencion",
        "jefatura",
    ]

    def get(self, request):
        count = Notification.objects.filter(
            usuario_destinatario=request.user,
            estado=Notification.EstadoChoices.ENVIADA,
        ).count()
        return JsonResponse({"count": count})


class NotificationDropdownView(RoleRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/_dropdown.html"
    context_object_name = "notifications"
    roles_requeridos = [
        "administrador",
        "rrhh",
        "ti",
        "finanzas",
        "logistica",
        "prevencion",
        "jefatura",
    ]

    def get_queryset(self):
        return Notification.objects.filter(
            usuario_destinatario=self.request.user,
            estado=Notification.EstadoChoices.ENVIADA,
        )[:10]
