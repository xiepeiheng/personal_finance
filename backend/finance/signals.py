from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver
from .models import Transaction, Category, Ledger, Transfer, Account


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


def _recalc_account(account_id):
    if account_id is None:
        return
    try:
        Account.objects.get(pk=account_id).recalculate()
    except Account.DoesNotExist:
        pass


# ─── Transaction signals ───

@receiver(pre_save, sender=Transaction)
def remember_old_category_and_account(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Transaction.objects.get(pk=instance.pk)
            instance._old_category_id = old.category_id
            instance._old_account_id = old.account_id
        except Transaction.DoesNotExist:
            instance._old_category_id = None
            instance._old_account_id = None
    else:
        instance._old_category_id = None
        instance._old_account_id = None


@receiver(post_save, sender=Transaction)
def update_amounts_on_save(sender, instance, **kwargs):
    _recalc_category(instance.category_id)
    old_cat_id = getattr(instance, "_old_category_id", None)
    if old_cat_id is not None and old_cat_id != instance.category_id:
        _recalc_category(old_cat_id)

    _recalc_account(instance.account_id)
    old_acc_id = getattr(instance, "_old_account_id", None)
    if old_acc_id is not None and old_acc_id != instance.account_id:
        _recalc_account(old_acc_id)


@receiver(post_delete, sender=Transaction)
def update_amounts_on_delete(sender, instance, **kwargs):
    _recalc_category(instance.category_id)
    _recalc_account(instance.account_id)


# ─── Transfer signals ───

@receiver(pre_save, sender=Transfer)
def remember_old_accounts(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Transfer.objects.get(pk=instance.pk)
            instance._old_from_account_id = old.from_account_id
            instance._old_to_account_id = old.to_account_id
        except Transfer.DoesNotExist:
            instance._old_from_account_id = None
            instance._old_to_account_id = None
    else:
        instance._old_from_account_id = None
        instance._old_to_account_id = None


@receiver(post_save, sender=Transfer)
def update_accounts_on_transfer_save(sender, instance, **kwargs):
    _recalc_account(instance.from_account_id)
    old_from_id = getattr(instance, "_old_from_account_id", None)
    if old_from_id is not None and old_from_id != instance.from_account_id:
        _recalc_account(old_from_id)

    _recalc_account(instance.to_account_id)
    old_to_id = getattr(instance, "_old_to_account_id", None)
    if old_to_id is not None and old_to_id != instance.to_account_id:
        _recalc_account(old_to_id)


@receiver(post_delete, sender=Transfer)
def update_accounts_on_transfer_delete(sender, instance, **kwargs):
    _recalc_account(instance.from_account_id)
    _recalc_account(instance.to_account_id)


# ─── Account signals ───

@receiver(post_save, sender=Account)
def update_account_on_save(sender, instance, **kwargs):
    _recalc_account(instance.id)


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
