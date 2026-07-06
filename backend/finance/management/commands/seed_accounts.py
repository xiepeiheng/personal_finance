from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from finance.models import Account, AccountType, Transaction

User = get_user_model()


class Command(BaseCommand):
    help = "创建初始账户（招商银行储蓄卡7258、投资账户）并关联历史交易记录"

    def handle(self, *args, **options):
        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.WARNING("没有用户，跳过"))
            return

        bank_type, _ = AccountType.objects.get_or_create(
            slug="bank", defaults={"name": "银行账户", "sort_order": 1}
        )
        securities_type, _ = AccountType.objects.get_or_create(
            slug="securities", defaults={"name": "证券账户", "sort_order": 2}
        )

        bank_accounts = 0
        invest_accounts = 0
        linked_tx = 0

        for user in users:
            bank, created = Account.objects.get_or_create(
                name="招商银行储蓄卡7258",
                user=user,
                defaults={
                    "account_type": bank_type,
                    "initial_balance": Decimal("0.00"),
                },
            )
            if created:
                self.stdout.write(f"  用户 {user.username}: 创建 {bank.name}")
                bank_accounts += 1

            invest, created = Account.objects.get_or_create(
                name="投资账户",
                user=user,
                defaults={
                    "account_type": securities_type,
                    "initial_balance": Decimal("0.00"),
                },
            )
            if created:
                self.stdout.write(f"  用户 {user.username}: 创建 {invest.name}")
                invest_accounts += 1

            updated = Transaction.objects.filter(
                account__isnull=True,
                category__time_ledger__user=user,
            ).update(account=bank)
            linked_tx += updated
            if updated:
                self.stdout.write(f"  用户 {user.username}: {updated} 条历史记录关联到 {bank.name}")

            bank.recalculate()
            invest.recalculate()

        self.stdout.write(self.style.SUCCESS(
            f"完成：创建银行账户 {bank_accounts} 个，投资账户 {invest_accounts} 个，关联历史记录 {linked_tx} 条"
        ))
