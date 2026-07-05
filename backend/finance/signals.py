from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from .models import Transaction, Category, Ledger


def _recalc_category(category_id):
    if category_id is None:
        return
    try:
        category = Category.objects.get(pk=category_id)
    except Category.DoesNotExist:
        return
    category.recalculate()
    for ledger_attr in ("time_ledger", "category_ledger"):
        ledger_id = getattr(category, ledger_attr + "_id", None)
        if ledger_id:
            try:
                Ledger.objects.get(pk=ledger_id).recalculate()
            except Ledger.DoesNotExist:
                pass


def _recalc_ledger(ledger_id):
    if ledger_id is None:
        return
    try:
        Ledger.objects.get(pk=ledger_id).recalculate()
    except Ledger.DoesNotExist:
        pass


# ─── Transaction signals ───

@receiver(pre_save, sender=Transaction)
def remember_old_category(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Transaction.objects.get(pk=instance.pk)
            instance._old_category_id = old.category_id
        except Transaction.DoesNotExist:
            instance._old_category_id = None
    else:
        instance._old_category_id = None


@receiver(post_save, sender=Transaction)
def update_amounts_on_save(sender, instance, **kwargs):
    _recalc_category(instance.category_id)
    old_id = getattr(instance, "_old_category_id", None)
    if old_id is not None and old_id != instance.category_id:
        _recalc_category(old_id)


@receiver(post_delete, sender=Transaction)
def update_amounts_on_delete(sender, instance, **kwargs):
    _recalc_category(instance.category_id)


# ─── Category signals ───

@receiver(pre_save, sender=Category)
def remember_old_ledgers(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Category.objects.get(pk=instance.pk)
            instance._old_time_ledger_id = old.time_ledger_id
            instance._old_category_ledger_id = old.category_ledger_id
        except Category.DoesNotExist:
            instance._old_time_ledger_id = None
            instance._old_category_ledger_id = None
    else:
        instance._old_time_ledger_id = None
        instance._old_category_ledger_id = None


@receiver(post_save, sender=Category)
def update_ledgers_on_category_save(sender, instance, **kwargs):
    for attr in ("time_ledger", "category_ledger"):
        new_id = getattr(instance, attr + "_id", None)
        old_id = getattr(instance, "_old_" + attr + "_id", None)
        if old_id is not None and old_id != new_id:
            _recalc_ledger(old_id)
        if new_id is not None:
            _recalc_ledger(new_id)


@receiver(post_delete, sender=Category)
def update_ledgers_on_category_delete(sender, instance, **kwargs):
    for attr in ("time_ledger", "category_ledger"):
        ledger_id = getattr(instance, attr + "_id", None)
        if ledger_id:
            _recalc_ledger(ledger_id)
