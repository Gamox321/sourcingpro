from django import forms
from apps.workers.models import Worker
from apps.clients.models import CostCenter
from .models import Process, Task


class ContratacionForm(forms.Form):
    run = forms.CharField(max_length=12, label='RUN',
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    nombre = forms.CharField(max_length=100, label='Nombre completo',
                             widget=forms.TextInput(attrs={'class': 'form-control'}))
    correo = forms.EmailField(label='Correo electrónico',
                              widget=forms.EmailInput(attrs={'class': 'form-control'}))
    cargo = forms.CharField(max_length=100, label='Cargo',
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
    centro_costo = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(estado='activo'),
        label='Centro de costo',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fecha_ingreso_estimada = forms.DateField(
        required=False, label='Fecha ingreso estimada',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )
    motivo = forms.CharField(required=False, label='Motivo',
                             widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


class CambioCeCoForm(forms.Form):
    trabajador = forms.ModelChoiceField(
        queryset=Worker.objects.filter(estado='activo'),
        label='Trabajador',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    ceco_destino = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(estado='activo'),
        label='Centro de costo destino',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fecha_estimada = forms.DateField(label='Fecha estimada',
                                     widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    motivo = forms.CharField(label='Motivo',
                             widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


class TerminoForm(forms.Form):
    trabajador = forms.ModelChoiceField(
        queryset=Worker.objects.filter(estado__in=['activo', 'por_egresar']),
        label='Trabajador',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fecha_termino = forms.DateField(label='Fecha de término',
                                    widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    motivo = forms.CharField(label='Motivo',
                             widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


class DespidoForm(forms.Form):
    trabajador = forms.ModelChoiceField(
        queryset=Worker.objects.filter(estado__in=['activo', 'por_egresar']),
        label='Trabajador',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    fecha_efectiva = forms.DateField(label='Fecha efectiva',
                                     widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    motivo = forms.CharField(label='Motivo',
                             widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    causal_legal = forms.CharField(label='Causal legal',
                                   widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


class TaskEstadoForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['estado']
        widgets = {'estado': forms.Select(attrs={'class': 'form-select'})}
