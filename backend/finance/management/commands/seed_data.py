from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from finance.models import Category, Ledger, Transaction
from users.constants import UserRole

try:
    from django.contrib.auth import get_user_model

    User = get_user_model()
except Exception:
    from django.contrib.auth.models import User


def _create_users():
    admin, _ = User.objects.get_or_create(username="admin")
    admin.is_superuser = True
    admin.set_password("admin")
    admin.save()

    user1, _ = User.objects.get_or_create(username="user1")
    user1.set_password("pass1234")
    user1.save()
    user1.groups.add(Group.objects.get_or_create(name=UserRole.USER)[0])

    return admin, user1


def _create_ledgers(user):
    ledgers_data = [
        ("2025年收支总账", "time"),
        ("2025年6月", "time"),
        ("日常三餐", "category"),
        ("出行旅游", "category"),
        ("服饰美容", "category"),
    ]
    ledgers = {}
    for name, ltype in ledgers_data:
        ledger, _ = Ledger.objects.get_or_create(
            name=name, ledger_type=ltype, user=user,
            defaults={"remarks": f"{name}测试账本"},
        )
        ledgers[name] = ledger
    return ledgers


def _create_categories(user, ledgers):
    categories_data = [
        dict(name="三餐", budget=3000, time_ledger=ledgers["2025年收支总账"], category_ledger=ledgers["日常三餐"]),
        dict(name="水果零食", budget=500, time_ledger=ledgers["2025年6月"], category_ledger=None),
        dict(name="交通出行", budget=1000, time_ledger=ledgers["2025年收支总账"], category_ledger=ledgers["出行旅游"]),
        dict(name="服饰", budget=2000, time_ledger=ledgers["2025年收支总账"], category_ledger=ledgers["服饰美容"]),
        dict(name="房租", budget=3000, time_ledger=ledgers["2025年收支总账"], category_ledger=None),
        dict(name="工资收入", budget=Decimal("15000"), time_ledger=ledgers["2025年收支总账"], category_ledger=None),
    ]
    categories = {}
    for kwargs in categories_data:
        cat, _ = Category.objects.get_or_create(
            name=kwargs["name"], time_ledger=kwargs["time_ledger"],
            defaults=kwargs,
        )
        categories[cat.name] = cat
    return categories


def _create_transactions(user, categories):
    today = date.today()
    transactions_data = [
        dict(category=categories["三餐"], trade_time=today - timedelta(days=1), partner="美团外卖", amount=Decimal("-35.50"), channel="微信支付"),
        dict(category=categories["三餐"], trade_time=today - timedelta(days=2), partner="沙县小吃", amount=Decimal("-22.00"), channel="支付宝"),
        dict(category=categories["三餐"], trade_time=today - timedelta(days=3), partner="超市便当", amount=Decimal("-18.90"), channel="微信支付"),
        dict(category=categories["水果零食"], trade_time=today - timedelta(days=1), partner="百果园", amount=Decimal("-45.00"), channel="支付宝"),
        dict(category=categories["水果零食"], trade_time=today - timedelta(days=5), partner="便利店", amount=Decimal("-12.50"), channel="微信支付"),
        dict(category=categories["交通出行"], trade_time=today - timedelta(days=1), partner="滴滴出行", amount=Decimal("-28.00"), channel="支付宝"),
        dict(category=categories["交通出行"], trade_time=today - timedelta(days=4), partner="地铁", amount=Decimal("-6.00"), channel="微信支付"),
        dict(category=categories["交通出行"], trade_time=today - timedelta(days=7), partner="滴滴出行", amount=Decimal("-35.00"), channel="支付宝"),
        dict(category=categories["服饰"], trade_time=today - timedelta(days=10), partner="优衣库", amount=Decimal("-399.00"), channel="支付宝", star=4),
        dict(category=categories["房租"], trade_time=date(today.year, today.month, 1), partner="房东", amount=Decimal("-2800.00"), channel="银行转账", remarks="6月房租"),
        dict(category=categories["工资收入"], trade_time=date(today.year, today.month, 15), partner="公司", amount=Decimal("15000.00"), channel="银行转账", star=5, remarks="6月工资"),
        dict(category=categories["三餐"], trade_time=today - timedelta(days=15), partner="海底捞", amount=Decimal("-256.00"), channel="支付宝", star=5, remarks="朋友聚餐"),
    ]
    for kwargs in transactions_data:
        Transaction.objects.get_or_create(
            category=kwargs["category"],
            trade_time=kwargs["trade_time"],
            partner=kwargs["partner"],
            amount=kwargs["amount"],
            defaults=kwargs,
        )


class Command(BaseCommand):
    help = "创建测试数据"

    def handle(self, *args, **options):
        self.stdout.write("Creating seed data...")

        admin, user1 = _create_users()
        self.stdout.write(f"  Users: admin/admin (superuser), user1/pass1234")

        ledgers = _create_ledgers(user1)
        self.stdout.write(f"  Ledgers: {len(ledgers)} created")

        categories = _create_categories(user1, ledgers)
        self.stdout.write(f"  Categories: {len(categories)} created")

        _create_transactions(user1, categories)
        self.stdout.write(f"  Transactions: 12 created")

        for ledger in ledgers.values():
            ledger.recalculate()
        for cat in categories.values():
            cat.recalculate()

        self.stdout.write(self.style.SUCCESS("Seed data created."))
        self.stdout.write("  admin  / admin    (superuser)")
        self.stdout.write("  user1  / pass1234 (regular user)")
