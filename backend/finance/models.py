from decimal import Decimal
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from utils.exceptions import BusinessException
from utils.code_enum import CodeEnum

User = get_user_model()


class Ledger(models.Model):
    """账本/维度集合
    ledger_type 区分两种角色：
    - time: 时间维度账本，如"2025年收支总账"
    - category: 分类维度账本，如"日常三餐"、"出游计划"
    """

    LEDGER_TYPE_CHOICES = [
        ("time", "时间维度"),
        ("category", "分类维度"),
    ]
    ledger_type = models.CharField(
        max_length=20,
        choices=LEDGER_TYPE_CHOICES,
        default="time",
        verbose_name="账本类型",
    )
    name = models.CharField(max_length=20, verbose_name="名称")
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="ledgers",
        verbose_name="所属用户",
    )
    balance = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="余额",
    )
    is_complete = models.BooleanField(default=False, verbose_name="是否完成")
    remarks = models.CharField(max_length=200, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "账本"
        verbose_name_plural = "账本"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_ledger_type_display()}] {self.name}"

    def recalculate(self):
        if self.ledger_type == "time":
            total = self.time_categories.aggregate(total=Sum("actual_amount"))["total"] or Decimal("0.00")
        else:
            total = self.category_categories.aggregate(total=Sum("actual_amount"))["total"] or Decimal("0.00")

        self.balance = total.quantize(Decimal("0.01"))
        self.save(update_fields=["balance", "updated_at"])


class Category(models.Model):
    """
    消费计划
    属于一个或两个 Ledger（time_ledger 和/或 category_ledger）。
    至少需要关联一个 Ledger。
    """
    name = models.CharField(max_length=100, verbose_name="名称")
    time_ledger = models.ForeignKey(
        Ledger,
        on_delete=models.PROTECT,
        related_name="time_categories",
        verbose_name="关联时间账本",
        null=True,
        blank=True,
    )
    category_ledger = models.ForeignKey(
        Ledger,
        on_delete=models.PROTECT,
        related_name="category_categories",
        verbose_name="关联分类账本",
        null=True,
        blank=True,
    )
    budget = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="预算金额",
    )
    actual_amount = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="实际金额",
    )
    is_complete = models.BooleanField(default=False, verbose_name="是否完成")
    star = models.PositiveIntegerField(default=0, verbose_name="满意度")
    remarks = models.CharField(max_length=200, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "消费计划"
        verbose_name_plural = "消费计划"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        if not self.time_ledger and not self.category_ledger:
            raise ValidationError("消费计划必须至少关联一个账本")

    def save(self, *args, **kwargs):
        self.full_clean(exclude={"actual_amount", "time_ledger", "category_ledger"})
        super().save(*args, **kwargs)

    def recalculate(self):
        from django.db.models import Sum

        total = self.transactions.aggregate(total=Sum("amount"))["total"] or Decimal(
            "0.00"
        )
        self.actual_amount = total.quantize(Decimal("0.01"))
        self.save(update_fields=["actual_amount", "updated_at"])


class Transaction(models.Model):
    """单条交易记录"""
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="所属分类",
    )
    trade_time = models.DateField(verbose_name="交易日期")
    partner = models.CharField(max_length=100, verbose_name="交易对象")
    amount = models.DecimalField(
        max_digits=11,
        decimal_places=2,
        verbose_name="金额",
    )
    star = models.PositiveIntegerField(default=0, verbose_name="满意度")
    channel = models.CharField(max_length=100, blank=True, verbose_name="交易渠道")
    detail = models.CharField(max_length=100, blank=True, verbose_name="交易细节")
    ticket_file = models.FileField(
        upload_to="tickets/%Y/%m/",
        blank=True,
        verbose_name="凭据",
    )
    remarks = models.CharField(max_length=200, blank=True, verbose_name="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "交易记录"
        verbose_name_plural = "交易记录"
        ordering = ["-trade_time", "-created_at"]

    def __str__(self):
        sign = "支出" if self.amount < 0 else "收入"
        return f"{self.trade_time} {self.partner} {sign} {abs(self.amount)}"

    def save(self, *args, **kwargs):
        if self.amount == 0:
            raise BusinessException(
                code=CodeEnum.AMOUNT_ZERO.code,
                message=CodeEnum.AMOUNT_ZERO.message,
                http_status=400,
            )
        super().save(*args, **kwargs)
