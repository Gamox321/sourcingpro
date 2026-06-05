from django.contrib import messages
from django.db import models as db_models
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from apps.accounts.decorators import RoleRequiredMixin
from .models import CostCenter, Client


class ClientListView(RoleRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    roles_requeridos = ['administrador', 'rrhh']
    paginate_by = 20

    def get_queryset(self):
        qs = Client.objects.all()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(db_models.Q(nombre__icontains=q) | db_models.Q(descripcion__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        return ctx


class ClientCreateView(RoleRequiredMixin, CreateView):
    model = Client
    template_name = 'clients/client_form.html'
    fields = ['nombre', 'descripcion']
    roles_requeridos = ['administrador', 'rrhh']
    success_url = reverse_lazy('clients:client_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)


class ClientUpdateView(RoleRequiredMixin, UpdateView):
    model = Client
    template_name = 'clients/client_form.html'
    fields = ['nombre', 'descripcion']
    roles_requeridos = ['administrador', 'rrhh']
    success_url = reverse_lazy('clients:client_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)


class CostCenterListView(RoleRequiredMixin, ListView):
    model = CostCenter
    template_name = 'clients/costcenter_list.html'
    context_object_name = 'costcenters'
    roles_requeridos = ['administrador']
    paginate_by = 20

    def get_queryset(self):
        qs = CostCenter.objects.select_related('cliente', 'jefatura')

        user = self.request.user
        if user.roles.filter(nombre='jefatura').exists():
            qs = qs.filter(jefatura=user)

        q = self.request.GET.get('q', '').strip()
        estado = self.request.GET.get('estado', '')
        if q:
            qs = qs.filter(
                db_models.Q(nombre__icontains=q) |
                db_models.Q(codigo__icontains=q) |
                db_models.Q(cliente__nombre__icontains=q)
            )
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '')
        ctx['filtro_estado'] = self.request.GET.get('estado', '')
        return ctx


class CostCenterDetailView(RoleRequiredMixin, DetailView):
    model = CostCenter
    template_name = 'clients/costcenter_detail.html'
    context_object_name = 'costcenter'
    roles_requeridos = ['administrador']

    def get_queryset(self):
        return CostCenter.objects.select_related('cliente', 'jefatura')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['trabajadores'] = self.object.trabajadores.all()
        return ctx


class CostCenterCreateView(RoleRequiredMixin, CreateView):
    model = CostCenter
    template_name = 'clients/costcenter_form.html'
    fields = ['nombre', 'codigo', 'cliente', 'jefatura']
    roles_requeridos = ['administrador', 'rrhh']
    success_url = reverse_lazy('clients:costcenter_list')

    def form_valid(self, form):
        messages.success(self.request, 'Centro de costo creado exitosamente.')
        return super().form_valid(form)


class CostCenterUpdateView(RoleRequiredMixin, UpdateView):
    model = CostCenter
    template_name = 'clients/costcenter_form.html'
    fields = ['nombre', 'codigo', 'cliente', 'jefatura', 'estado']
    roles_requeridos = ['administrador', 'rrhh']
    success_url = reverse_lazy('clients:costcenter_list')

    def form_valid(self, form):
        messages.success(self.request, 'Centro de costo actualizado exitosamente.')
        return super().form_valid(form)


class CostCenterDeactivateView(RoleRequiredMixin, View):
    roles_requeridos = ['administrador', 'rrhh']

    def post(self, request, pk):
        costcenter = CostCenter.objects.get(pk=pk)
        if costcenter.estado == CostCenter.EstadoChoices.INACTIVO:
            costcenter.estado = CostCenter.EstadoChoices.ACTIVO
            messages.success(request, 'Centro de costo reactivado.')
        else:
            if costcenter.trabajadores.filter(
                estado__in=['activo', 'en_transito']
            ).exists():
                messages.error(
                    request,
                    'No se puede desactivar: tiene trabajadores activos o en tránsito. '
                    'Inicia un proceso de cambio de CeCo para ellos primero.'
                )
                return redirect('clients:costcenter_detail', pk=pk)
            costcenter.estado = CostCenter.EstadoChoices.INACTIVO
            messages.success(request, 'Centro de costo desactivado.')
        costcenter.save(update_fields=['estado'])
        return redirect('clients:costcenter_list')
