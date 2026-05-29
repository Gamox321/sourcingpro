from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.audit.middleware import get_current_user

from apps.accounts.models import User as UserModel
from apps.clients.models import Client, CostCenter
from apps.workers.models import Worker, CostCenterHistory
from apps.inventory.models import AssetType, Asset, AssetAssignment
from apps.processes.models import Process, Task


TRACKED_MODELS = {
    'Worker': Worker,
    'Process': Process,
    'Task': Task,
    'CostCenter': CostCenter,
    'Asset': Asset,
    'AssetAssignment': AssetAssignment,
    'User': UserModel,
}


def _get_table_name(model):
    return model._meta.db_table


def _serialize(instance):
    data = {}
    for field in instance._meta.fields:
        name = field.name
        value = getattr(instance, name)
        if hasattr(value, 'isoformat'):
            value = str(value)
        if isinstance(value, (int, float, str, bool, type(None))):
            data[name] = value
        else:
            try:
                data[name] = str(value)
            except Exception:
                data[name] = None
    return data


def _get_accion(created, old_data, new_data):
    if created:
        return AuditLog.AccionChoices.CREACION
    if old_data and old_data.get('estado') != new_data.get('estado'):
        return AuditLog.AccionChoices.CAMBIO_ESTADO
    return AuditLog.AccionChoices.MODIFICACION


def _log_action(instance, accion, old_data=None, new_data=None, descripcion=None):
    user = get_current_user()
    if not user or not user.is_authenticated:
        return

    AuditLog.objects.create(
        tabla_afectada=_get_table_name(instance.__class__),
        accion=accion,
        descripcion=descripcion or f'{accion} en {instance._meta.verbose_name}',
        valor_anterior=old_data,
        valor_nuevo=new_data or _serialize(instance),
        usuario=user,
        id_entidad_afectada=instance.pk,
    )


_pre_save_data = {}


@receiver(pre_save, sender=Worker)
@receiver(pre_save, sender=Process)
@receiver(pre_save, sender=Task)
@receiver(pre_save, sender=CostCenter)
@receiver(pre_save, sender=Asset)
@receiver(pre_save, sender=AssetAssignment)
@receiver(pre_save, sender=UserModel)
def audit_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            _pre_save_data[(sender, instance.pk)] = _serialize(old)
        except sender.DoesNotExist:
            pass


@receiver(post_save, sender=Worker)
@receiver(post_save, sender=Process)
@receiver(post_save, sender=Task)
@receiver(post_save, sender=CostCenter)
@receiver(post_save, sender=Asset)
@receiver(post_save, sender=AssetAssignment)
@receiver(post_save, sender=UserModel)
def audit_post_save(sender, instance, created, **kwargs):
    new_data = _serialize(instance)
    old_data = _pre_save_data.pop((sender, instance.pk), None)
    accion = _get_accion(created, old_data, new_data)
    _log_action(instance, accion, old_data=old_data, new_data=new_data)


@receiver(post_delete, sender=Worker)
@receiver(post_delete, sender=Process)
@receiver(post_delete, sender=Task)
@receiver(post_delete, sender=CostCenter)
@receiver(post_delete, sender=Asset)
@receiver(post_delete, sender=AssetAssignment)
@receiver(post_delete, sender=UserModel)
def audit_post_delete(sender, instance, **kwargs):
    old_data = _pre_save_data.pop((sender, instance.pk), None)
    user = get_current_user()
    if user and user.is_authenticated:
        AuditLog.objects.create(
            tabla_afectada=_get_table_name(sender),
            accion=AuditLog.AccionChoices.ELIMINACION_LOGICA,
            descripcion=f'Eliminación de {instance._meta.verbose_name} #{instance.pk}',
            valor_anterior=old_data or _serialize(instance),
            usuario=user,
            id_entidad_afectada=instance.pk,
        )
