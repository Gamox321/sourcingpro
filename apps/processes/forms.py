import re

from django import forms
from django.core.exceptions import ValidationError

from apps.workers.models import Worker
from apps.clients.models import CostCenter
from .models import Process


RUN_RE = re.compile(r"^\d{7,8}-[\dkK]$")


class ContratacionForm(forms.Form):
    run = forms.CharField(
        max_length=12,
        label="RUN",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "12345678-9"}
        ),
    )
    nombre = forms.CharField(
        max_length=100,
        label="Nombre completo",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Juan Perez Garcia"}
        ),
    )
    correo = forms.EmailField(
        label="Correo electronico",
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "juan.perez@empresa.cl"}
        ),
    )
    cargo = forms.CharField(
        max_length=100,
        label="Cargo",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Analista de Sistemas"}
        ),
    )
    centro_costo = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(estado=CostCenter.EstadoChoices.ACTIVO),
        label="Centro de costo",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    fecha_ingreso_estimada = forms.DateField(
        required=False,
        label="Fecha ingreso estimada",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    motivo = forms.CharField(
        required=False,
        label="Motivo",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    def __init__(self, *args, **kwargs):
        user_cecos = kwargs.pop("user_cecos", None)
        super().__init__(*args, **kwargs)
        if user_cecos is not None:
            self.fields["centro_costo"].queryset = self.fields[
                "centro_costo"
            ].queryset.filter(pk__in=user_cecos.values_list("pk", flat=True))

    def clean_run(self):
        run = self.cleaned_data.get("run", "").strip()
        if not RUN_RE.match(run):
            raise ValidationError(
                "Formato RUN invalido. Use 12345678-9 (sin puntos, con guion y digito verificador)."
            )
        if Worker.objects.filter(run=run).exists():
            raise ValidationError("Ya existe un trabajador con este RUN.")
        return run

    def clean_correo(self):
        correo = self.cleaned_data.get("correo", "").strip()
        if Worker.objects.filter(correo=correo).exists():
            raise ValidationError("Ya existe un trabajador con este correo.")
        return correo


class CambioCeCoForm(forms.Form):
    trabajador = forms.ModelChoiceField(
        queryset=Worker.objects.filter(estado=Worker.EstadoChoices.ACTIVO),
        label="Trabajador",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    ceco_destino = forms.ModelChoiceField(
        queryset=CostCenter.objects.filter(estado=CostCenter.EstadoChoices.ACTIVO),
        label="Centro de costo destino",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    fecha_estimada = forms.DateField(
        label="Fecha estimada",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    motivo = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    def __init__(self, *args, **kwargs):
        user_cecos = kwargs.pop("user_cecos", None)
        super().__init__(*args, **kwargs)
        if user_cecos is not None:
            self.fields["ceco_destino"].queryset = self.fields[
                "ceco_destino"
            ].queryset.filter(pk__in=user_cecos.values_list("pk", flat=True))
            self.fields["trabajador"].queryset = self.fields[
                "trabajador"
            ].queryset.filter(centro_costo_actual__in=user_cecos)

    def clean_trabajador(self):
        worker = self.cleaned_data.get("trabajador")
        if worker and worker.estado != Worker.EstadoChoices.ACTIVO:
            raise ValidationError(
                f'El trabajador esta en estado "{worker.get_estado_display()}". '
                "Solo trabajadores activos pueden cambiar de CeCo."
            )
        if (
            worker
            and Process.objects.filter(
                trabajador=worker,
                tipo=Process.TipoChoices.CAMBIO_CECO,
                estado=Process.EstadoChoices.EN_CURSO,
            ).exists()
        ):
            raise ValidationError(
                "Este trabajador ya tiene un cambio de CeCo en curso."
            )
        return worker

    def clean(self):
        cleaned_data = super().clean()
        worker = cleaned_data.get("trabajador")
        ceco_destino = cleaned_data.get("ceco_destino")
        if worker and ceco_destino and worker.centro_costo_actual == ceco_destino:
            raise ValidationError(
                f"El trabajador ya pertenece a {ceco_destino.nombre}. "
                "Seleccione un centro de costo diferente."
            )
        return cleaned_data


class TerminoForm(forms.Form):
    trabajador = forms.ModelChoiceField(
        queryset=Worker.objects.filter(
            estado__in=[Worker.EstadoChoices.ACTIVO, Worker.EstadoChoices.POR_EGRESAR]
        ),
        label="Trabajador",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    fecha_termino = forms.DateField(
        label="Fecha de termino",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    motivo = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    def __init__(self, *args, **kwargs):
        user_cecos = kwargs.pop("user_cecos", None)
        super().__init__(*args, **kwargs)
        if user_cecos is not None:
            self.fields["trabajador"].queryset = self.fields[
                "trabajador"
            ].queryset.filter(centro_costo_actual__in=user_cecos)

    def clean_trabajador(self):
        worker = self.cleaned_data.get("trabajador")
        if (
            worker
            and Process.objects.filter(
                trabajador=worker,
                tipo=Process.TipoChoices.TERMINO,
                estado=Process.EstadoChoices.EN_CURSO,
            ).exists()
        ):
            raise ValidationError(
                "Este trabajador ya tiene un proceso de termino en curso."
            )
        return worker


class DespidoForm(forms.Form):
    trabajador = forms.ModelChoiceField(
        queryset=Worker.objects.filter(
            estado__in=[Worker.EstadoChoices.ACTIVO, Worker.EstadoChoices.POR_EGRESAR]
        ),
        label="Trabajador",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    fecha_efectiva = forms.DateField(
        label="Fecha efectiva",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    motivo = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
    causal_legal = forms.CharField(
        label="Causal legal",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    def __init__(self, *args, **kwargs):
        user_cecos = kwargs.pop("user_cecos", None)
        super().__init__(*args, **kwargs)
        if user_cecos is not None:
            self.fields["trabajador"].queryset = self.fields[
                "trabajador"
            ].queryset.filter(centro_costo_actual__in=user_cecos)

    def clean_trabajador(self):
        worker = self.cleaned_data.get("trabajador")
        if (
            worker
            and Process.objects.filter(
                trabajador=worker,
                tipo=Process.TipoChoices.DESPIDO,
                estado=Process.EstadoChoices.EN_CURSO,
            ).exists()
        ):
            raise ValidationError(
                "Este trabajador ya tiene un proceso de despido en curso."
            )
        return worker


class AsignacionActivosForm(forms.Form):
    trabajador = forms.ModelChoiceField(
        queryset=Worker.objects.filter(estado="activo").order_by("nombre"),
        label="Trabajador",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Selecciona el trabajador que recibira el equipo TI.",
    )
    comentario = forms.CharField(
        required=False,
        max_length=500,
        label="Comentario",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Tipo de equipo, sucursal, urgencia...",
            }
        ),
        help_text="Sugerencia opcional sobre el equipo a asignar.",
    )

    def __init__(self, *args, **kwargs):
        user_cecos = kwargs.pop("user_cecos", None)
        super().__init__(*args, **kwargs)
        if user_cecos is not None:
            self.fields["trabajador"].queryset = self.fields[
                "trabajador"
            ].queryset.filter(
                centro_costo_actual__in=user_cecos,
            )


class AsignacionEPPForm(forms.Form):
    trabajador = forms.ModelChoiceField(
        queryset=Worker.objects.filter(estado=Worker.EstadoChoices.ACTIVO).order_by("nombre"),
        label="Trabajador",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Selecciona el trabajador que recibira el EPP.",
    )
    comentario = forms.CharField(
        required=False,
        max_length=500,
        label="Comentario",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Tipo de EPP, urgencia...",
            }
        ),
        help_text="Sugerencia opcional sobre el EPP a asignar.",
    )

    def __init__(self, *args, **kwargs):
        user_cecos = kwargs.pop("user_cecos", None)
        super().__init__(*args, **kwargs)
        if user_cecos is not None:
            self.fields["trabajador"].queryset = self.fields[
                "trabajador"
            ].queryset.filter(
                centro_costo_actual__in=user_cecos,
            )
